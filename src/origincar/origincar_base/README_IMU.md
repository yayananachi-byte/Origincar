# Origincar Base - RDK IMU + EKF 融合说明

## 📋 功能概述

本包使用 **D-Robotics RDK X5 板载 BMI088 IMU** 作为唯一的 IMU 数据源，并通过 **EKF (Extended Kalman Filter)** 融合轮式里程计和 IMU 数据，输出更精确的融合里程计。

### 系统架构

```
┌──────────────────────────────────────┐
│   RDK X5 板载 BMI088 (I2C 接口)     │
└──────────────┬───────────────────────┘
               │
               ↓
┌──────────────────────────────────────┐
│  rdk_imu_driver.py (Python Node)    │
│  - 100Hz 数据更新                    │
│  - 发布 /imu/data_raw                │
│  - 发布 /imu/temperature             │
└──────────────┬───────────────────────┘
               │
               ↓ /imu/data_raw (sensor_msgs/Imu)
┌──────────────────────────────────────┐
│  ekf_filter_node                     │
│  (robot_localization)                │
│                                      │
│  输入:                               │
│  - /odom (轮式里程计 from serial)   │
│  - /imu/data_raw (RDK IMU)          │
│                                      │
│  EKF 融合算法                        │
│  ↓                                   │
│  输出:                               │
│  - /odom_combined ⭐ (融合里程计)   │
└──────────────┬───────────────────────┘
               │
               ↓ /odom_combined
        导航、定位、控制使用
```

## 🚀 快速启动

### 1. 标准启动（使用 RDK IMU）

```bash
cd /home/sunrise/RacingDev/dev_ws
source setup_origicar_env.sh

# 方式 1: 使用启动脚本（推荐）
bash start_origicar.sh

# 方式 2: 直接使用 launch 文件
ros2 launch origincar_base origincar_bringup.launch.py
```

### 2. 阿克曼模式启动

```bash
bash start_origicar.sh --akmcar
```

## 📡 主要话题

### 发布的话题

- **`/imu/data_raw`** (sensor_msgs/Imu)
  - RDK IMU 原始数据
  - 频率: 100Hz
  - 包含加速度、角速度数据

- **`/imu/temperature`** (std_msgs/Float32)
  - IMU 板载温度
  - 单位: °C

- **`/odom`** (nav_msgs/Odometry)
  - 轮式里程计（来自下位机串口）

- **`/odom_combined`** (nav_msgs/Odometry) ⭐
  - EKF 融合后的里程计
  - 融合了轮式里程计和 IMU 数据
  - **推荐使用此话题进行导航和控制**

### 订阅的话题

- **`/cmd_vel`** (geometry_msgs/Twist)
  - 差速模式速度控制

- **`/ackermann_cmd`** (ackermann_msgs/AckermannDriveStamped)
  - 阿克曼模式速度控制

- **`/set_pose`** (geometry_msgs/PoseWithCovarianceStamped)
  - 重置 EKF 位姿（详见 SET_POSE_USAGE.md）

## 📁 配置文件

### EKF 配置

- **`config/ekf_rdk_imu.yaml`**
  - RDK IMU 的 EKF 融合参数
  - 融合策略：
    - 轮式里程计: x, y, yaw, vx, vy, vyaw (差分模式)
    - IMU: yaw, vyaw (绝对模式)
    - 移除重力加速度影响

### Launch 文件

- **`launch/origincar_bringup.launch.py`**
  - 主启动文件
  - 自动启动：
    - 底盘节点（串口通信）
    - RDK IMU 驱动节点
    - EKF 融合节点
    - TF 变换

- **`launch/base_serial.launch.py`**
  - 底盘串口通信节点

- **`launch/robot_mode_description.launch.py`**
  - 机器人模型描述

## 🔧 高级配置

### 修改 IMU 发布频率

编辑 `launch/origincar_bringup.launch.py`:

```python
rdk_imu_driver_node = launch_ros.actions.Node(
    package='origincar_base',
    executable='rdk_imu_driver.py',
    parameters=[{
        'publish_rate': 100.0,  # 修改此值（默认 100Hz）
        'frame_id': 'imu_link',
        'use_gpio': True
    }]
)
```

### 禁用 GPIO LED 控制

如果不需要 LED 提示，可以禁用 GPIO:

```python
parameters=[{
    'publish_rate': 100.0,
    'frame_id': 'imu_link',
    'use_gpio': False  # 禁用 GPIO
}]
```

## 🧪 测试与验证

### 1. 检查 IMU 数据

```bash
# 查看 IMU 原始数据
ros2 topic echo /imu/data_raw

# 查看温度数据
ros2 topic echo /imu/temperature

# 查看数据频率
ros2 topic hz /imu/data_raw
```

### 2. 检查 EKF 融合结果

```bash
# 查看融合后的里程计
ros2 topic echo /odom_combined

# 比较轮式里程计和融合里程计
ros2 topic echo /odom
ros2 topic echo /odom_combined
```

### 3. 可视化

```bash
# 使用 rviz2 查看
rviz2

# 添加显示项：
# - Odometry: /odom_combined
# - TF: 查看坐标系变换
# - Imu: /imu/data_raw
```

## 📝 注意事项

1. **唯一 IMU 源**: 系统只使用 RDK X5 板载 IMU，不再支持下位机 MPU6050 或外部 BMI088

2. **I2C 权限**: 确保当前用户有 I2C 访问权限
   ```bash
   sudo usermod -aG i2c $USER
   # 重新登录生效
   ```

3. **GPIO 权限**: LED 控制需要 root 或 gpio 组权限
   ```bash
   sudo usermod -aG gpio $USER
   ```

4. **EKF 调优**: 如果融合效果不理想，可以调整 `config/ekf_rdk_imu.yaml` 中的协方差参数

5. **TF 坐标系**: 
   - `base_footprint`: 底盘中心
   - `imu_link`: IMU 安装位置（当前设置为与 base_footprint 重合）
   - 如需调整 IMU 位置，修改 `base_to_gyro` 的 static_transform_publisher 参数

## 🐛 故障排查

### IMU 无法初始化

```bash
# 检查 I2C 设备
i2cdetect -y 1

# 手动测试 RDK IMU
cd /home/sunrise/RacingDev/dev_ws/src/origincar/rdk_imu-library/Py_RDK_IMU
python3 test_pyimu.py
```

### EKF 没有输出

```bash
# 检查 EKF 节点状态
ros2 node info /ekf_filter_node

# 查看 EKF 日志
ros2 launch origincar_base origincar_bringup.launch.py 2>&1 | grep ekf

# 确认输入话题是否有数据
ros2 topic hz /odom
ros2 topic hz /imu/data_raw
```

### TF 变换问题

```bash
# 查看 TF 树
ros2 run tf2_tools view_frames.py
evince frames.pdf

# 检查特定变换
ros2 run tf2_ros tf2_echo base_footprint odom_combined
```

## 📚 相关文档

- **SET_POSE_USAGE.md**: EKF 位姿重置详细说明
- **RDK IMU Library**: `/home/sunrise/RacingDev/dev_ws/src/origincar/rdk_imu-library/README.md`

## 🔄 更新日志

- **2026-04-08**: 
  - ✅ 移除所有其他 IMU 支持（MPU6050, BMI088 I2C module）
  - ✅ 仅使用 RDK X5 板载 IMU 作为唯一数据源
  - ✅ 简化启动流程，移除条件判断
  - ✅ 优化 EKF 配置
