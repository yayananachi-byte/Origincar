# EKF 位姿重置使用说明

## 📚 概述

从 ROS2 Foxy 开始，`origincar_base` 已改用**官方的 `/set_pose` 方案**进行 EKF 位姿重置。

## ✅ 改进内容

### 移除的组件
- ❌ `odom_resetter.py` 节点（偏移量方案）
- ❌ `odom_resetter.launch.py` 启动文件
- ❌ `/odom_combined_raw` 中间话题
- ❌ `/reset_odom` 服务

### 新增特性
- ✅ EKF 直接输出 `/odom_combined`（无中间层）
- ✅ 支持通过 `/set_pose` 话题重置位姿
- ✅ TF 变换与里程计数据完全同步
- ✅ 符合 `robot_localization` 官方标准

## 🔧 使用方法

### 1. 启动 EKF 节点

```bash
# 使用 BMI088 IMU
ros2 launch origincar_base origincar_base_complete.launch.py use_bmi088:=true

# 使用 MPU6050 IMU（默认）
ros2 launch origincar_base origincar_base_complete.launch.py

# 或使用另一个启动文件（功能相同）
ros2 launch origincar_base origincar_bringup.launch.py
```

### 2. 发布位姿重置指令

#### 方法 A：使用 ROS2 命令行工具

```bash
# 重置到原点 (0, 0, 0)
ros2 topic pub --once /set_pose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'odom_combined'}, \
   pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, \
                 orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, \
         covariance: [0.01, 0.0, 0.0, 0.0, 0.0, 0.0, \
                      0.0, 0.01, 0.0, 0.0, 0.0, 0.0, \
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
                      0.0, 0.0, 0.0, 0.01, 0.0, 0.0, \
                      0.0, 0.0, 0.0, 0.0, 0.01, 0.0, \
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.01]}}"
```

#### 方法 B：在上位机代码中发布

**Python 示例：**

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped

class PoseResetNode(Node):
    def __init__(self):
        super().__init__('pose_reset_node')
        self.publisher = self.create_publisher(
            PoseWithCovarianceStamped, 
            '/set_pose', 
            10
        )
    
    def reset_to_origin(self):
        """重置位姿到原点"""
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom_combined'
        
        # 设置位姿为原点
        msg.pose.pose.position.x = 0.0
        msg.pose.pose.position.y = 0.0
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.w = 1.0
        
        # 设置协方差（小值表示高置信度）
        msg.pose.covariance = [
            0.01, 0.0,  0.0,  0.0, 0.0, 0.0,
            0.0,  0.01, 0.0,  0.0, 0.0, 0.0,
            0.0,  0.0,  0.0,  0.0, 0.0, 0.0,
            0.0,  0.0,  0.0,  0.01, 0.0, 0.0,
            0.0,  0.0,  0.0,  0.0, 0.01, 0.0,
            0.0,  0.0,  0.0,  0.0, 0.0,  0.01
        ]
        
        self.publisher.publish(msg)
        self.get_logger().info('✅ 已发布位姿重置指令到 /set_pose')

def main():
    rclpy.init()
    node = PoseResetNode()
    node.reset_to_origin()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**C++ 示例：**

```cpp
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose_with_covariance_stamped.hpp"

class PoseResetNode : public rclcpp::Node
{
public:
    PoseResetNode() : Node("pose_reset_node")
    {
        publisher_ = this->create_publisher<geometry_msgs::msg::PoseWithCovarianceStamped>(
            "/set_pose", 10);
    }
    
    void resetToOrigin()
    {
        auto msg = geometry_msgs::msg::PoseWithCovarianceStamped();
        msg.header.stamp = this->now();
        msg.header.frame_id = "odom_combined";
        
        // 设置位姿为原点
        msg.pose.pose.position.x = 0.0;
        msg.pose.pose.position.y = 0.0;
        msg.pose.pose.position.z = 0.0;
        msg.pose.pose.orientation.w = 1.0;
        
        // 设置协方差
        msg.pose.covariance = {
            0.01, 0.0,  0.0,  0.0, 0.0, 0.0,
            0.0,  0.01, 0.0,  0.0, 0.0, 0.0,
            0.0,  0.0,  0.0,  0.0, 0.0, 0.0,
            0.0,  0.0,  0.0,  0.01, 0.0, 0.0,
            0.0,  0.0,  0.0,  0.0, 0.01, 0.0,
            0.0,  0.0,  0.0,  0.0, 0.0,  0.01
        };
        
        publisher_->publish(msg);
        RCLCPP_INFO(this->get_logger(), "✅ 已发布位姿重置指令到 /set_pose");
    }

private:
    rclcpp::Publisher<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr publisher_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PoseResetNode>();
    node->resetToOrigin();
    rclcpp::shutdown();
    return 0;
}
```

#### 方法 C：在上位机 GUI 中集成

在您的 Web 监控界面或控制面板中添加"重置位姿"按钮，点击后发布 `/set_pose` 消息。

## 📊 数据流架构

```
上位机或其他控制节点
       ↓
发布 /set_pose (geometry_msgs/PoseWithCovarianceStamped)
       ↓
EKF 节点 (robot_localization/ekf_node)
  - 接收 /set_pose 消息
  - 重置内部状态估计
  - 更新卡尔曼滤波器协方差
       ↓
自动输出：
  ✅ /odom_combined (nav_msgs/Odometry)
  ✅ TF: odom_combined → base_footprint
```

## ✅ 验证方法

### 1. 检查话题列表

```bash
# 查看 EKF 输出的话题
ros2 topic list | grep odom
# 应该看到：/odom_combined（不再有 /odom_combined_raw）
```

### 2. 查看话题信息

```bash
# 查看谁在发布 /odom_combined
ros2 topic info /odom_combined -v
# 预期：Publisher 包含 ekf_filter_node
```

### 3. 验证 TF 变换

```bash
# 查看 TF 树
ros2 run tf2_tools view_frames

# 检查 TF 变换
ros2 run tf2_ros tf2_echo odom_combined base_footprint
```

### 4. 测试位姿重置

```bash
# ① 先查看当前位姿
ros2 topic echo /odom_combined | head -20

# ② 发布重置指令
ros2 topic pub --once /set_pose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: 'odom_combined'}, \
   pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, \
                 orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, \
         covariance: [0.01, 0.0, 0.0, 0.0, 0.0, 0.0, \
                      0.0, 0.01, 0.0, 0.0, 0.0, 0.0, \
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
                      0.0, 0.0, 0.0, 0.01, 0.0, 0.0, \
                      0.0, 0.0, 0.0, 0.0, 0.01, 0.0, \
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.01]}}"

# ③ 立即再次查看位姿（应该接近 0）
ros2 topic echo /odom_combined | head -20

# ④ 检查 TF 是否同步
ros2 run tf2_ros tf2_echo odom_combined base_footprint
```

## 🎯 优势对比

| 特性 | 旧方案（偏移量） | 新方案（/set_pose） |
|------|----------------|-------------------|
| **代码复杂度** | 高（150+ 行） | 低（调用接口） |
| **TF 同步** | ❌ 不同步 | ✅ 自动同步 |
| **四元数运算** | ✅ 手动处理 | ❌ 不需要 |
| **时间戳对齐** | ✅ 手动处理 | ❌ 不需要 |
| **协方差传递** | ✅ 手动复制 | ✅ 自动处理 |
| **官方支持** | ❌ 自己实现 | ✅ 官方接口 |
| **维护成本** | 高 | 低 |
| **可靠性** | 中等 | 高 |

## ⚠️ 注意事项

1. **坐标系必须正确**：`/set_pose` 消息的 `header.frame_id` 必须是 `odom_combined`
2. **协方差设置**：建议使用较小的值（如 0.01）表示高置信度
3. **时间戳**：应使用当前时间戳或 0（EKF 都能处理）
4. **TF 发布**：EKF 配置中的 `publish_tf` 必须为 `true`（默认就是）

## 📁 相关文件路径

- **EKF 配置文件**：
  - `dev_ws/src/origincar/origincar_base/config/ekf_bmi088.yaml`
  - `dev_ws/src/origincar/origincar_base/config/ekf_mpu6050.yaml`

- **Launch 文件**：
  - `dev_ws/src/origincar/origincar_base/launch/origincar_bringup.launch.py`
  - `dev_ws/src/origincar/origincar_base/launch/ekf.launch.py`

- **编译后重新加载环境**：
  ```bash
  cd ~/RacingDev/dev_ws
  colcon build --packages-select origincar_base
  source install/setup.bash
  ```

## 🆘 故障排查

### 问题 1：发布 /set_pose 后没有反应

**检查清单**：
```bash
# ① 确认 EKF 节点正在运行
ros2 node list | grep ekf

# ② 确认 /set_pose 话题存在
ros2 topic list | grep set_pose

# ③ 查看是否有其他节点订阅
ros2 topic info /set_pose -v

# ④ 检查 EKF 配置中的 publish_tf 参数
cat dev_ws/src/origincar/origincar_base/config/ekf*.yaml | grep publish_tf
# 应该是 true
```

### 问题 2：TF 变换不存在

```bash
# 查看完整的 TF 树
ros2 run tf2_tools view_frames
# 打开生成的 frames.pdf 查看

# 检查特定变换
ros2 run tf2_ros tf2_monitor odom_combined base_footprint
```

### 问题 3：编译错误

```bash
# 清理构建缓存
cd ~/RacingDev/dev_ws
colcon clean

# 重新编译
colcon build --packages-select origincar_base

# 加载环境
source install/setup.bash
```

## 📝 历史变更

- **2026-03-31**：移除 `odom_resetter` 节点，改用官方 `/set_pose` 方案
- **之前版本**：使用偏移量方案（存在 TF 不同步问题）

## 📚 参考资料

- [robot_localization 官方文档](https://cra-ros-pkg.github.io/robot_localization/)
- [REP 105 - Coordinate Frames](https://www.ros.org/reps/rep-0105.html)
- [geometry_msgs/PoseWithCovarianceStamped](https://docs.ros2.org/latest/api/geometry_msgs/msg/PoseWithCovarianceStamped.html)
