# Racing Image Collect

ROS2 图像数据采集工具，用于智能赛车项目的训练数据收集。

## 功能

- 📸 从摄像头订阅压缩图像并保存到本地
- 🎯 自动生成双数据集：
  - **障碍物检测**：完整图像 (640×480) → `detection_*.jpg`
  - **赛道检测**：底部裁剪 (640×224) → `line_follow_*.jpg`
- ⚙️ 可配置采集频率、保存路径等参数

## 快速开始

### 1. 启动系统

```bash
bash start_origicar.sh
```

系统会自动发布压缩图像到 `/image` 话题。

### 2. 启动采集

```bash
source install/setup.bash
ros2 launch racing_image_collect racing_image_collect.launch.py
```

或使用自定义参数：

```bash
ros2 launch racing_image_collect racing_image_collect.launch.py \
  sub_img_topic:=/image \
  fps:=5.0 \
  track_img_folder:=my_track_data \
  obstacle_img_folder:=my_obstacle_data
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sub_img_topic` | `/image` | 订阅的图像话题 |
| `track_img_folder` | `track_image1` | 赛道数据集路径 |
| `obstacle_img_folder` | `obstacle_image1` | 障碍物数据集路径 |
| `fps` | `2.0` | 采集频率（帧/秒） |

## 输出示例

```
img_collected/
├── track/                  # 赛道检测数据集
│   ├── line_follow_0001.jpg  (640×224, ~33KB)
│   ├── line_follow_0002.jpg
│   └── ...
└── obstacle/               # 障碍物检测数据集
    ├── detection_0001.jpg  (640×480, ~87KB)
    ├── detection_0002.jpg
    └── ...
```

## 技术细节

- **图像来源**：`hobot_usb_cam` 直接发布 CompressedImage 到 `/image`
- **消息类型**：`sensor_msgs/msg/CompressedImage` (JPEG格式)
- **自动适配**：节点自动检测话题类型并处理
