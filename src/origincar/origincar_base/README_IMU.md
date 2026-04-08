# Origincar Base IMU 切换功能说明

## 📋 功能概述

本包支持两种 IMU 传感器的切换使用：
- **MPU6050** (下位机板载) - **默认配置**，通过串口通信获取数据
- **BMI088** (RDK IMU Module) - 通过 I2C 通信（需要硬件连接）

## 🚀 快速启动

### 1. 默认启动（使用 MPU6050 IMU - 下位机）

```bash
cd /home/sunrise/RacingDev/dev_ws
source install/setup.bash

# 方式 1: 使用完整启动文件（推荐）
ros2 launch origincar_base origincar_base_complete.launch.py
```

**说明**：默认情况下 `use_bmi088=false`，使用下位机的 MPU6050 IMU。

### 2. 切换到 BMI088 IMU（需要硬件连接）

```bash
# 切换到 BMI088 IMU
ros2 launch origincar_base origincar_base_complete.launch.py use_bmi088:=true
```

**注意**：使用 BMI088 前需要：
1. 连接 BMI088 硬件到 RDK X5 的 I2C 接口
2. 安装 Python 依赖：`pip3 install smbus2`
3. 将拨码开关切换到 I2C 一侧

## ⚙️ 参数说明

### `use_bmi088` (default: false)
- **false** (默认): 使用 MPU6050 IMU（来自下位机串口）
- **true**: 使用 BMI088 IMU（I2C 接口）

### `akmcar` (default: false)
- **false**: 差速底盘模式
- **true**: 阿克曼转向模式

### `use_sim_time` (default: false)
- **false**: 使用系统时间
- **true**: 使用仿真时间

## 📁 配置文件

### EKF 配置文件位置
- **MPU6050 配置** (默认): `config/ekf_mpu6050.yaml`
- **BMI088 配置**: `config/ekf_bmi088.yaml`

## 🔍 验证 IMU 数据

### 查看当前 IMU 数据

```bash
# 启动系统（默认使用 MPU6050）
ros2 launch origincar_base origincar_base_complete.launch.py

# 在另一个终端查看 IMU 数据
ros2 topic echo /imu/data_raw
```

### 查看 EKF 融合结果

```bash
# 查看融合后的里程计
ros2 topic echo /odom_combined
```

## 📊 话题列表

### IMU 话题
- `/imu/data_raw` (sensor_msgs/Imu) - IMU 原始数据
  - 默认来源：MPU6050（下位机串口）
  - 可选来源：BMI088（I2C 接口）

### 共享话题
- `/odom` (nav_msgs/Odometry) - 轮式里程计
- `/odom_combined` (nav_msgs/Odometry) - EKF 融合后的里程计
- `/set_pose` (geometry_msgs/PoseWithCovarianceStamped) - **位姿重置接口**（官方方案）
- `/robotpose` (origincar_msg/Data) - 机器人位置
- `/robotvel` (origincar_msg/Data) - 机器人速度
- `/PowerVoltage` (std_msgs/Float32) - 电池电压

## 🎯 推荐配置

### 当前配置（默认）
```bash
# 使用下位机 MPU6050 IMU
ros2 launch origincar_base origincar_base_complete.launch.py
```

适用于：
- ✅ BMI088 硬件未连接时
- ✅ 测试和调试阶段
- ✅ 使用现有下位机系统

### 未来配置（当 BMI088 连接后）
```bash
# 使用 BMI088 IMU
ros2 launch origincar_base origincar_base_complete.launch.py use_bmi088:=true
```

适用于：
- ✅ BMI088 硬件已连接
- ✅ 需要更高精度 IMU 数据
- ✅ 高级导航和定位应用

## 🛠️ 硬件准备（BMI088）

当你准备好使用 BMI088 时：

### 1. 安装依赖
```bash
pip3 install smbus2
```

### 2. 硬件连接
- SDA → RDK X5 I2C_SDA (Pin 3)
- SCL → RDK X5 I2C_SCL (Pin 5)
- VCC → 3.3V
- GND → GND

### 3. 拨码开关设置
- 将拨码开关切换到 **I2C** 一侧

### 4. 验证设备
```bash
i2cdetect -y 1
# 应该能看到 0x19 (加速度计) 和 0x69 (陀螺仪)
```

## 📝 注意事项

1. **默认行为**：系统默认使用下位机的 MPU6050 IMU，无需任何额外配置

2. **切换 IMU**：每次切换 IMU 类型后，EKF 会重新初始化状态估计

3. **兼容性**：两种 IMU 都发布到相同的话题 `/imu/data_raw`，可以无缝切换

4. **位姿重置**：
   - ✅ **新方案**：使用官方 `/set_pose` 话题重置 EKF 位姿
   - ✅ **TF 同步**：EKF 自动更新 TF 变换，确保数据一致性
   - 📖 **详细说明**：参考 `SET_POSE_USAGE.md`

5. **性能差异**：
   - MPU6050（下位机）：满足基本需求，依赖下位机固件
   - BMI088（I2C）：更高精度、更高频率（100Hz）、更好的温度特性

## 📚 相关文件

- BMI088 驱动：`scripts/bmi088_imu_driver.py`
- BMI088 启动：`launch/bmi088_imu.launch.py`
- EKF 配置：`config/ekf_mpu6050.yaml`, `config/ekf_bmi088.yaml`
- 完整启动：`launch/origincar_base_complete.launch.py`
- **位姿重置说明**：`SET_POSE_USAGE.md`
