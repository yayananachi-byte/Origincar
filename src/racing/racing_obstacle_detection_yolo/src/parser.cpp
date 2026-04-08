// Copyright (c) 2022，Horizon Robotics.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "racing_obstacle_detection/parser.h"

#include "rapidjson/document.h"
#include "rapidjson/istreamwrapper.h"
#include "rapidjson/writer.h"

#include <memory>
#include <opencv2/opencv.hpp>
#include <opencv2/dnn/dnn.hpp>

using hobot::dnn_node::DNNTensor;

namespace hobot {
namespace dnn_node {
namespace racing_obstacle_detection {
// 算法输出解析参数
float score_threshold_ = 0.25;  // 降低阈值，配合更好的筛选策略
float nms_threshold_ = 0.45;    // 标准 NMS 阈值
int nms_top_k_ = 300;           // 增加候选框数量

// Sigmoid 查找表优化 (0-10 范围，精度 0.001)
const int LUT_SIZE = 10000;
const float LUT_SCALE = 1000.0f;
static float sigmoid_lut[LUT_SIZE];
static bool lut_initialized = false;

// 初始化查找表
void init_lookup_tables() {
  if (lut_initialized) return;
  
  for (int i = 0; i < LUT_SIZE; i++) {
    float x = -5.0f + (float)i / LUT_SCALE;
    sigmoid_lut[i] = 1.0f / (1.0f + std::exp(-x));
  }
  lut_initialized = true;
}

// 快速 sigmoid 近似 (使用查找表)
inline float fast_sigmoid(float x) {
  if (x < -5.0f) return 0.0f;
  if (x > 5.0f) return 1.0f;
  int idx = (int)((x + 5.0f) * LUT_SCALE);
  if (idx < 0) idx = 0;
  if (idx >= LUT_SIZE) idx = LUT_SIZE - 1;
  return sigmoid_lut[idx];
}



void ParseTensor(std::shared_ptr<DNNTensor> tensor,
                 int layer,
                 std::vector<cv::Rect2d>& boxes,
                 std::vector<float>& scores,
                 std::vector<int>& class_ids,
                 PTQYolo5Config &yolo5_config);

void yolo5_nms(std::vector<cv::Rect2d>& boxes,
               std::vector<float>& scores,
               std::vector<int>& class_ids,
               float confidence_threshold,
               float nms_threshold,
               int top_k,
               std::vector<std::shared_ptr<YoloV5Result>>& result);

int get_tensor_hw(std::shared_ptr<DNNTensor> tensor, int *height, int *width);

/**
 * Finds the greatest element in the range [first, last)
 * @tparam[in] ForwardIterator: iterator type
 * @param[in] first: fist iterator
 * @param[in] last: last iterator
 * @return Iterator to the greatest element in the range [first, last)
 */
template <class ForwardIterator>
inline size_t argmax(ForwardIterator first, ForwardIterator last) {
  return std::distance(first, std::max_element(first, last));
}

void ParseTensor(std::shared_ptr<DNNTensor> tensor,
                 int layer,
                 std::vector<cv::Rect2d>& boxes,
                 std::vector<float>& scores,
                 std::vector<int>& class_ids,
                 PTQYolo5Config &yolo5_config) {
  hbSysFlushMem(&(tensor->sysMem[0]), HB_SYS_MEM_CACHE_INVALIDATE);
  int num_classes = yolo5_config.class_num;
  int stride = yolo5_config.strides[layer];
  int num_pred = yolo5_config.class_num + 4 + 1;

  std::vector<std::pair<double, double>> &anchors =
      yolo5_config.anchors_table[layer];

  int height, width;
  auto ret = get_tensor_hw(tensor, &height, &width);
  if (ret != 0) {
    RCLCPP_ERROR(rclcpp::get_logger("Yolo5_detection_parser"),
                 "get_tensor_hw failed");
    return;
  }

  int anchor_num = anchors.size();
  auto *data = reinterpret_cast<float *>(tensor->sysMem[0].virAddr);
  
  // 预分配内存，减少动态分配开销
  int estimated_objects = (height * width * anchor_num) / 5;
  boxes.reserve(boxes.size() + estimated_objects);
  scores.reserve(scores.size() + estimated_objects);
  class_ids.reserve(class_ids.size() + estimated_objects);
  
  // 初始化查找表
  init_lookup_tables();
  
  // 优化：预先计算 grid 坐标，避免内层循环重复计算
  for (int h = 0; h < height; h++) {
    for (int w = 0; w < width; w++) {
      for (int k = 0; k < anchor_num; k++) {
        double anchor_x = anchors[k].first;
        double anchor_y = anchors[k].second;
        float *cur_data = data + k * num_pred;
        
        // 优化 1: 先检查 objectness，快速跳过大量背景
        float obj_score = cur_data[4];
        if (obj_score < score_threshold_ * 0.5) {  // 使用更宽松的阈值进行初筛
          continue;
        }
        
        // 优化 2: 找到最大类别分数
        int class_id = 5;
        float max_class_score = cur_data[5];
        for (int c = 6; c < num_classes + 5; c++) {
          if (cur_data[c] > max_class_score) {
            max_class_score = cur_data[c];
            class_id = c;
          }
        }
        
        // 优化 3: 计算最终置信度，不合格直接跳过
        float confidence = fast_sigmoid(obj_score) * fast_sigmoid(max_class_score);
        if (confidence < score_threshold_) {
          continue;
        }
        
        // 优化 4: 特征解码（只计算通过筛选的框）
        float center_x = ((fast_sigmoid(cur_data[0]) * 2.0f - 0.5f) + w) * stride;
        float center_y = ((fast_sigmoid(cur_data[1]) * 2.0f - 0.5f) + h) * stride;
        float box_w = std::pow(fast_sigmoid(cur_data[2]) * 2.0f, 2) * anchor_x;
        float box_h = std::pow(fast_sigmoid(cur_data[3]) * 2.0f, 2) * anchor_y;
        
        float x1 = center_x - box_w / 2.0f;
        float y1 = center_y - box_h / 2.0f;
        float x2 = center_x + box_w / 2.0f;
        float y2 = center_y + box_h / 2.0f;
        
        // 边界检查
        if (x2 <= 0 || y2 <= 0 || x1 > x2 || y1 > y2) {
          continue;
        }
        
        // 添加到结果中
        boxes.emplace_back(x1, y1, box_w, box_h);
        scores.push_back(confidence);
        class_ids.push_back(class_id - 5);
      }
      data = data + num_pred * anchors.size();
    }
  }
}



void yolo5_nms(std::vector<cv::Rect2d>& boxes,
               std::vector<float>& scores,
               std::vector<int>& class_ids,
               float confidence_threshold,
               float nms_threshold,
               int top_k,
               std::vector<std::shared_ptr<YoloV5Result>>& result) {
  // 使用 OpenCV 的高效 NMS 实现
  std::vector<int> indices;
  cv::dnn::NMSBoxes(boxes, scores, confidence_threshold, nms_threshold, indices, 1.0f, top_k);
  
  // 将 NMS 结果转换为需要的格式
  result.reserve(indices.size());
  for (int idx : indices) {
    const cv::Rect2d& box = boxes[idx];
    auto yolo_res = std::make_shared<YoloV5Result>(
        class_ids[idx],
        box.x,
        box.y,
        box.x + box.width,
        box.y + box.height,
        scores[idx],
        "object");  // class_name 会在后续填充
    result.push_back(yolo_res);
  }
}

int get_tensor_hw(std::shared_ptr<DNNTensor> tensor, int *height, int *width) {
  int h_index = 0;
  int w_index = 0;
  if (tensor->properties.tensorLayout == HB_DNN_LAYOUT_NHWC) {
    h_index = 1;
    w_index = 2;
  } else if (tensor->properties.tensorLayout == HB_DNN_LAYOUT_NCHW) {
    h_index = 2;
    w_index = 3;
  } else {
    return -1;
  }
  *height = tensor->properties.validShape.dimensionSize[h_index];
  *width = tensor->properties.validShape.dimensionSize[w_index];
  return 0;
}

int32_t Parse(
    const std::shared_ptr<hobot::dnn_node::DnnNodeOutput> &node_output,
    std::vector<std::shared_ptr<YoloV5Result>> &results,
    PTQYolo5Config &yolo5_config) {
  // 优化：使用分离的存储结构，最后再合并
  std::vector<cv::Rect2d> all_boxes;
  std::vector<float> all_scores;
  std::vector<int> all_class_ids;
  
  // 预分配内存
  all_boxes.reserve(1000);
  all_scores.reserve(1000);
  all_class_ids.reserve(1000);
  
  // 解析每个输出层
  for (size_t i = 0; i < node_output->output_tensors.size(); i++) {
    ParseTensor(
        node_output->output_tensors[i], static_cast<int>(i), 
        all_boxes, all_scores, all_class_ids, yolo5_config);
  }
  
  // 一次性 NMS
  yolo5_nms(all_boxes, all_scores, all_class_ids, 
            score_threshold_, nms_threshold_, nms_top_k_, results);
  
  // 填充类别名称
  for (auto& res : results) {
    if (res->id >= 0 && res->id < (int)yolo5_config.class_names.size()) {
      res->class_name = yolo5_config.class_names[res->id];
    } else {
      res->class_name = "unknown";
    }
  }

  return 0;
}

}  // namespace racing_obstacle_detection
}  // namespace dnn_node
}  // namespace hobot