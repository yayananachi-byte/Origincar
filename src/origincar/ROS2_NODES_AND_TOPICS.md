# Origicar ROS2 系统节点与话题总览

**生成时间**: 2026-04-14 (最新更新)  
**上次更新**: 2026-04-08  
**系统配置**: RDK X5 板载 IMU + EKF 融合 + USB 摄像头 + ROSBridge + 图像压缩中继  
**启动模式**: 差速驱动模式

---

## 📊 系统架构概览

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  RDK IMU Driver │────▶│              │     │                 │
│  (BMI088)       │     │              │     │                 │
│  100Hz          │     │   EKF Filter │────▶│  /odom_combined │
└─────────────────┘     │   Node       │     │  (融合里程计)    │
                        │              │     └─────────────────┘
┌─────────────────┐     │              │
│  Origicar Base  │────▶│              │
│  (轮式里程计)    │     └──────────────┘
│  /odom          │
└─────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  USB Camera     │────▶│  Codec Encoder   │────▶│  /image     │
│  (hobot_usb_cam)│     │  (JPEG压缩)       │     │  (MJPEG)    │
└─────────────────┘     └──────────────────┘     └─────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   WebSocket     │
                                              │   (Web显示)      │
                                              └─────────────────┘

┌─────────────────┐
│  ROSBridge      │◀──── ws://192.168.31.214:9090
│  (端口 9090)    │
└─────────────────┘
```

---

## 🚀 运行中的 ROS2 节点 (共 17 个)

### 1. `/origincar_base` - 底盘控制节点
**功能**: 底盘驱动、电机控制、轮式里程计计算

| 类型 | 话题名称 | 消息类型 | **帧率** | 说明 |
|------|---------|---------|---------|------|
| **订阅** | `/cmd_vel` | `geometry_msgs/msg/Twist` | - | 速度控制指令 |
| **订阅** | `/none` | `ackermann_msgs/msg/AckermannDriveStamped` | - | 阿克曼控制（未使用） |
| **发布** | `/PowerVoltage` | `std_msgs/msg/Float32` | **~18 Hz** | 电池电压 |
| **发布** | `/odom` | `nav_msgs/msg/Odometry` | **~20 Hz** | 轮式里程计 |
| **发布** | `/robotpose` | `origincar_msg/msg/Data` | **~18 Hz** | 机器人位姿数据 |
| **发布** | `/robotvel` | `origincar_msg/msg/Data` | **~18 Hz** | 机器人速度数据 |
| **发布** | `/tf` | `tf2_msgs/msg/TFMessage` | **~11 Hz** | 坐标变换 |

**服务**: 标准参数管理服务（describe/get/set/list_parameters）

---

### 2. `/rdk_imu_driver` - RDK IMU 驱动节点
**功能**: RDK X5 板载 BMI088 IMU 数据采集

| 类型 | 话题名称 | 消息类型 | **帧率** | 说明 |
|------|---------|---------|---------|------|
| **发布** | `/imu/data_raw` | `sensor_msgs/msg/Imu` | **~100 Hz** | IMU 原始数据（加速度+角速度） |
| **发布** | `/imu/temperature` | `std_msgs/msg/Float32` | **~100 Hz** | IMU 温度数据 |

**特性**:
- 接口: SPI
- 加速度计量程: ±24g
- 陀螺仪量程: ±2000 dps
- 发布频率: 100 Hz

---

### 3. `/ekf_filter_node` - EKF 融合节点
**功能**: 扩展卡尔曼滤波，融合轮式里程计和 IMU 数据

| 类型 | 话题名称 | 消息类型 | QoS | **帧率** | 说明 |
|------|---------|---------|-----|---------|------|
| **订阅** | `/odom` | `nav_msgs/msg/Odometry` | BEST_EFFORT | ~20 Hz | 轮式里程计输入 |
| **订阅** | `/imu/data_raw` | `sensor_msgs/msg/Imu` | BEST_EFFORT | ~100 Hz | IMU 数据输入 |
| **订阅** | `/set_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | RELIABLE | - | 位姿重置指令 |
| **发布** | `/odom_combined` | `nav_msgs/msg/Odometry` | RELIABLE | **~30 Hz** ⬆️ | ⭐ 融合后的里程计 |
| **发布** | `/tf` | `tf2_msgs/msg/TFMessage` | RELIABLE | **~11 Hz** | 融合后的坐标变换 |
| **发布** | `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | - | **低频** | 诊断信息 |

**服务**:
- `/enable` - 启用滤波器
- `/toggle` - 切换滤波处理
- `/set_pose` - 设置初始位姿

**重要**: `/odom_combined` 是系统的主要里程计输出，用于导航和定位。实测频率约 30 Hz。

---

### 4. `/hobot_usb_cam` - USB 摄像头节点
**功能**: USB 摄像头图像采集和压缩

| 类型 | 话题名称 | 消息类型 | **帧率** | 说明 |
|------|---------|---------|---------|------|
| **发布** | `/image` | `sensor_msgs/msg/CompressedImage` | **~24 fps** | MJPEG 压缩图像 |
| **发布** | `/camera_info` | `sensor_msgs/msg/CameraInfo` | **单次发布** | 相机标定信息 |

**服务**:
- `/set_capture` - 控制采集开关

**图像格式**: Motion-JPEG (MJPEG)  
**分辨率**: 640x480  
**实测帧率**: ~14 fps（当前实际运行频率）

---

### 5. `/image_relay` - 图像话题中继节点 ⭐ 新增
**功能**: 使用 topic_tools relay 将 `/image` 复制为 `/image/compressed`

| 类型 | 话题名称 | 消息类型 | QoS | **帧率** | 说明 |
|------|---------|---------|-----|---------|------|
| **订阅** | `/image` | `sensor_msgs/msg/CompressedImage` | default | ~14 fps | 接收原始压缩图像 |
| **发布** | `/image/compressed` | `sensor_msgs/msg/CompressedImage` | default | **~14 fps** | 复制的压缩图像话题 |

**特性**: 
- 零延迟话题复制
- 不修改图像数据
- 用于兼容需要 `/image/compressed` 话题的节点（如 racing_image_collect）

---

### 6. `/hobot_codec_decoder` - 硬件解码节点
**功能**: Hobot 硬件图像解码（从 ROS 到共享内存）

| 类型 | 话题名称 | 消息类型 | QoS | **帧率** | 说明 |
|------|---------|---------|-----|---------|------|
| **订阅** | `/image` | `sensor_msgs/msg/CompressedImage` | RELIABLE | ~14 fps | 接收压缩图像 |
| **发布** | `/hbmem_img` | `hbm_img_msgs/msg/HbmMsg1080P` | BEST_EFFORT | **~14 fps** | 共享内存图像 |

**特性**: 
- 使用 Hobot X5 硬件解码器
- JPEG → NV12 格式转换
- 零拷贝传输优化
- 供 AI 推理节点使用

---

### 7. `/websocket` - WebSocket 图像传输节点
**功能**: 通过 WebSocket 传输图像到 Web 前端

| 类型 | 话题名称 | 消息类型 | **帧率** | 说明 |
|------|---------|---------|---------|------|
| **订阅** | `/image` | `sensor_msgs/msg/CompressedImage` | ~14 fps | 接收图像用于 Web 显示 |

**参数**:
- `image_topic`: /image
- `image_type`: mjpeg
- `only_show_image`: 0
- `smart_topic`: /none_smart_data

**注意**: 当前无 AI 数据发布者，会显示警告信息

---

### 8. `/image_compressor` - 图像压缩节点 ⭐ 新增
**功能**: 将未压缩图像转换为 CompressedImage 格式（备用方案）

| 类型 | 话题名称 | 消息类型 | QoS | **帧率** | 说明 |
|------|---------|---------|-----|---------|------|
| **订阅** | `/image_raw` | `sensor_msgs/msg/Image` | default | - | 接收未压缩图像 |
| **发布** | `/image/compressed` | `sensor_msgs/msg/CompressedImage` | default | - | 发布压缩图像 |

**状态**: ⚠️ 当前未使用（`/image_raw` 无发布者）  
**用途**: 备用方案，当需要从 Image 转换为 CompressedImage 时启用

---

### 9. `/joint_state_publisher` - 关节状态发布节点

| 类型 | 话题名称 | 消息类型 | **帧率** | 说明 |
|------|---------|---------|---------|------|
| **订阅** | `/robot_description` | `std_msgs/msg/String` | 单次 | URDF 描述 |
| **发布** | `/joint_states` | `sensor_msgs/msg/JointState` | **~10 Hz** | 关节状态 |

---

### 9. `/joint_state_publisher` - 关节状态发布节点
**功能**: 发布机器人关节状态

| 类型 | 话题名称 | 消息类型 | **帧率** | 说明 |
|------|---------|---------|---------|------|
| **订阅** | `/robot_description` | `std_msgs/msg/String` | 单次 | URDF 描述 |
| **发布** | `/joint_states` | `sensor_msgs/msg/JointState` | **~10 Hz** | 关节状态 |

---

### 10. `/robot_state_publisher` - 机器人状态发布节点
**功能**: 提供 WebSocket 接口，允许 Web 客户端访问 ROS2

| 类型 | 话题名称 | 消息类型 | 说明 |
|------|---------|---------|------|
| **发布** | `/client_count` | `std_msgs/msg/Int32` | 客户端连接数 |
| **发布** | `/connected_clients` | `rosbridge_msgs/msg/ConnectedClients` | 连接的客户端列表 |

**监听地址**: `ws://0.0.0.0:9090`  
**外部访问**: `ws://192.168.31.214:9090`

**支持的功能**:
- Advertise/Publish/Subscribe
- Call Service/Advertise Service
- Send Action Goal/Action Feedback/Action Result

---

### 11. `/rosbridge_websocket` - ROSBridge WebSocket 服务器
**功能**: 提供 WebSocket 接口，允许 Web 客户端访问 ROS2

| 类型 | 话题名称 | 消息类型 | 说明 |
|------|---------|---------|------|
| **发布** | `/client_count` | `std_msgs/msg/Int32` | 客户端连接数 |
| **发布** | `/connected_clients` | `rosbridge_msgs/msg/ConnectedClients` | 连接的客户端列表 |

**监听地址**: `ws://0.0.0.0:9090`  
**外部访问**: `ws://192.168.31.214:9090`

**支持的功能**:
- Advertise/Publish/Subscribe
- Call Service/Advertise Service
- Send Action Goal/Action Feedback/Action Result

---

### 12. `/rosapi` & `/rosapi_params` - ROS API 服务节点

## 📡 主要话题详细列表

### 控制类话题

#### `/cmd_vel`
- **类型**: `geometry_msgs/msg/Twist`
- **发布者**: 无（等待外部控制）
- **订阅者**: `/origincar_base`
- **用途**: 发送线速度和角速度控制指令
- **QoS**: RELIABLE

#### `/none` (阿克曼控制)
- **类型**: `ackermann_msgs/msg/AckermannDriveStamped`
- **发布者**: 无
- **订阅者**: `/origincar_base`
- **用途**: 阿克曼转向模式控制（当前未使用）

---

### 里程计类话题

#### `/odom` ⭐
- **类型**: `nav_msgs/msg/Odometry`
- **发布者**: `/origincar_base`
- **订阅者**: `/ekf_filter_node`
- **用途**: 轮式里程计（仅基于编码器）
- **QoS**: RELIABLE
- **注意**: 这是 EKF 的输入之一，不直接用于导航

#### `/odom_combined` ⭐⭐⭐
- **类型**: `nav_msgs/msg/Odometry`
- **发布者**: `/ekf_filter_node`
- **订阅者**: 无（可通过 ROSBridge 订阅）
- **帧率**: **~30 Hz** ⬆️ (实测)
- **用途**: **融合里程计**（轮式里程计 + IMU），系统主要里程计输出
- **QoS**: RELIABLE
- **重要性**: 导航、定位、建图应使用此话题

---

### IMU 类话题

#### `/imu/data_raw`
- **类型**: `sensor_msgs/msg/Imu`
- **发布者**: `/rdk_imu_driver`
- **订阅者**: `/ekf_filter_node`
- **帧率**: ~100 Hz
- **用途**: IMU 原始数据（加速度计 + 陀螺仪）
- **QoS**: RELIABLE (发布) / BEST_EFFORT (订阅)

#### `/imu/temperature`
- **类型**: `std_msgs/msg/Float32`
- **发布者**: `/rdk_imu_driver`
- **订阅者**: 无
- **帧率**: ~1 Hz
- **用途**: IMU 芯片温度监控

---

### 图像类话题

#### `/image`
- **类型**: `sensor_msgs/msg/CompressedImage`
- **发布者**: 
  - `/hobot_usb_cam` (唯一发布者)
- **订阅者**: 
  - `/hobot_codec_decoder` (硬件解码)
  - `/websocket` (Web 传输)
  - `/image_relay` (话题中继)
- **格式**: Motion-JPEG (MJPEG)
- **分辨率**: 640x480
- **帧率**: **~14 fps** (当前实测)
- **用途**: 视频流传输和显示

#### `/image/compressed` ⭐ 新增
- **类型**: `sensor_msgs/msg/CompressedImage`
- **发布者**: 
  - `/image_relay` (从 /image 复制)
  - `/image_compressor` (备用，当前未使用)
- **订阅者**: 无（可供 racing_image_collect 等节点订阅）
- **帧率**: **~14 fps** (与 /image 同步)
- **用途**: 兼容需要 `/image/compressed` 话题的节点

#### `/camera_info`
- **类型**: `sensor_msgs/msg/CameraInfo`
- **发布者**: `/hobot_usb_cam`
- **订阅者**: 无
- **用途**: 相机内参和畸变系数（当前无标定文件）

#### `/hbmem_img`
- **类型**: `hbm_img_msgs/msg/HbmMsg1080P`
- **发布者**: `/hobot_codec_decoder`
- **订阅者**: `/hobot_codec_encoder`
- **QoS**: BEST_EFFORT
- **用途**: 共享内存图像传输（零拷贝优化）

---

### 系统信息类话题

#### `/PowerVoltage`
- **类型**: `std_msgs/msg/Float32`
- **发布者**: `/origincar_base`
- **订阅者**: 无（可通过 ROSBridge 订阅）
- **用途**: 电池电压监控

#### `/robotpose`
- **类型**: `origincar_msg/msg/Data`
- **发布者**: `/origincar_base`
- **订阅者**: 无
- **用途**: 机器人位姿数据（自定义消息）

#### `/robotvel`
- **类型**: `origincar_msg/msg/Data`
- **发布者**: `/origincar_base`
- **订阅者**: 无
- **用途**: 机器人速度数据（自定义消息）

---

### TF 变换类话题

#### `/tf`
- **类型**: `tf2_msgs/msg/TFMessage`
- **发布者**: 
  - `/origincar_base`
  - `/robot_state_publisher`
  - `/ekf_filter_node`
- **订阅者**: `/transform_listener_impl_*`
- **用途**: 动态坐标变换（base_link → odom 等）

#### `/tf_static`
- **类型**: `tf2_msgs/msg/TFMessage`
- **发布者**: 静态变换发布器
- **用途**: 静态坐标变换（base_link → camera 等）

---

### 位姿重置话题

#### `/set_pose` ⭐
- **类型**: `geometry_msgs/msg/PoseWithCovarianceStamped`
- **发布者**: 无（等待外部发布）
- **订阅者**: `/ekf_filter_node`
- **用途**: **重置 EKF 位姿**，用于初始化或校正机器人位置
- **QoS**: RELIABLE
- **使用方法**: 发布包含初始位姿和协方差的消息到此话题

---

### ROSBridge 相关话题

#### `/client_count`
- **类型**: `std_msgs/msg/Int32`
- **发布者**: `/rosbridge_websocket`
- **用途**: 当前 WebSocket 客户端数量

#### `/connected_clients`
- **类型**: `rosbridge_msgs/msg/ConnectedClients`
- **发布者**: `/rosbridge_websocket`
- **用途**: 连接的客户端详细信息

---

### 其他话题

#### `/joint_states`
- **类型**: `sensor_msgs/msg/JointState`
- **发布者**: `/joint_state_publisher`
- **订阅者**: `/robot_state_publisher`
- **用途**: 机器人关节状态

#### `/robot_description`
- **类型**: `std_msgs/msg/String`
- **发布者**: `/robot_state_publisher`
- **订阅者**: `/joint_state_publisher`
- **Durability**: TRANSIENT_LOCAL
- **用途**: URDF 机器人描述

#### `/diagnostics`
- **类型**: `diagnostic_msgs/msg/DiagnosticArray`
- **发布者**: `/ekf_filter_node`
- **用途**: EKF 滤波器诊断信息

#### `/parameter_events`
- **类型**: `rcl_interfaces/msg/ParameterEvent`
- **用途**: 参数变更事件（所有节点）

#### `/rosout`
- **类型**: `rcl_interfaces/msg/Log`
- **用途**: ROS 日志输出（所有节点）

---

## 🔧 坐标变换树 (TF Tree)

```
odom (EKF 融合坐标系)
  └── base_footprint (机器人底部中心)
        ├── base_link (机器人本体坐标系)
        │     ├── board_link (主板)
        │     ├── up_left_Link (左前轮)
        │     ├── up_right_Link (右前轮)
        │     ├── down_left_Link (左后轮)
        │     └── down_right_Link (右后轮)
        ├── gyro_link (IMU 坐标系)
        └── camera (相机坐标系)
```

**静态变换**:
- `base_footprint` → `base_link`: (0.41, 0.12, 0.0)
- `base_footprint` → `gyro_link`: (0.0, 0.0, 0.0)

**动态变换**:
- `odom` → `base_footprint`: 由 EKF 滤波器发布

---

## 📊 数据流向总结

### 里程计融合流程
```
轮式编码器 → /odom ──┐
                      ├──→ EKF Filter → /odom_combined → 导航系统
IMU (BMI088) → /imu/data_raw ──┘
```

### 图像处理流程
```
USB 摄像头 → hobot_usb_cam → /image (MJPEG, ~14 fps)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
          image_relay      hobot_codec_decoder   websocket
          (话题复制)       (JPEG→NV12解码)      (Web传输)
                    ↓               ↓
          /image/compressed   /hbmem_img (共享内存)
          (~14 fps)           (供AI推理使用)
```

### 控制流程
```
外部控制 → /cmd_vel → origincar_base → 电机驱动
                     ↓
                  /odom (轮式里程计)
```

---

## 🌐 ROSBridge 访问信息

**WebSocket 地址**:
- 本地: `ws://localhost:9090`
- 网络: `ws://192.168.31.214:9090`

**可订阅的主要话题**:
- `/odom_combined` - 融合里程计（推荐）
- `/imu/data_raw` - IMU 数据
- `/image` - 摄像头图像
- `/PowerVoltage` - 电池电压
- `/tf` - 坐标变换

**可发布的话题**:
- `/cmd_vel` - 速度控制
- `/set_pose` - 位姿重置

---

## 💡 使用建议

### 1. 导航和定位
- ✅ 使用 `/odom_combined` 作为里程计源
- ❌ 不要直接使用 `/odom`（未经过 IMU 融合）

### 2. 位姿初始化
- 发布消息到 `/set_pose` 话题来重置 EKF 位姿
- 格式: `geometry_msgs/PoseWithCovarianceStamped`

### 3. 图像查看
- 通过 ROSBridge 订阅 `/image` 话题
- 或使用 Foxglove Studio 连接 `ws://192.168.31.214:9090`

### 4. 速度控制
- 发布 `geometry_msgs/Twist` 到 `/cmd_vel`
- 线性速度: `linear.x` (m/s)
- 角速度: `angular.z` (rad/s)

### 5. 系统监控
- 订阅 `/PowerVoltage` 监控电池电量
- 订阅 `/diagnostics` 查看 EKF 状态
- 订阅 `/imu/temperature` 监控 IMU 温度

---

## ⚠️ 注意事项

1. **ROSBridge 参数修复**: 已修复 `delay_between_messages` 参数类型问题（从整数改为浮点数 0.0）

2. **EKF 融合**: 系统使用 RDK X5 板载 BMI088 IMU 与轮式里程计进行 EKF 融合，提供更高精度的里程计数据

3. **图像传输**: 使用 Hobot 硬件编解码器实现高效图像传输，支持零拷贝优化

4. **坐标变换**: TF 树由多个节点共同维护，确保坐标变换的一致性

5. **服务可用性**: 所有节点都提供标准的 ROS2 参数管理服务

---

## 📝 更新日志

- **2026-04-14 (最新)**: 
  - **新增 `/image_relay` 节点**：使用 topic_tools relay 复制 `/image` 到 `/image/compressed`
  - **新增 `/image_compressor` 节点**：备用图像压缩方案（当前未使用）
  - **更新 EKF 频率**：`/odom_combined` 实测 ~30 Hz（从 20 Hz 提升）
  - **更新图像频率**：`/image` 实测 ~14 fps（受硬件影响）
  - **优化图像流架构**：
    - `/hobot_usb_cam` → `/image` (唯一发布者)
    - `/image_relay` → `/image/compressed` (话题复制，供 racing_image_collect 使用)
    - `/hobot_codec_decoder` → `/hbmem_img` (AI 推理用)
  - **移除 hobot_codec_encoder**：简化图像流，避免重复编码

- **2026-04-08 (更新)**:
  - **禁用 hobot_codec_encoder 节点**，简化图像流
  - **统一图像参数**: 640x480 @ 30fps
  - **图像流向优化**: 
    - `/hobot_usb_cam` → `/image` (唯一发布者)
    - `/websocket` 订阅 `/image` 用于 Web 显示
    - `/hobot_codec_decoder` 订阅 `/image` → `/hbmem_img` (供 AI 推理使用)
  - 添加 RDK X5 板载 IMU 支持
  - 实现 EKF 融合架构
  - 修复 ROSBridge 参数类型错误
  - 生成系统节点和话题总览文档
  - **添加所有话题的实测发布频率**

---

## 📊 话题发布频率总结

### 高频话题 (≥50 Hz)

| 话题名称 | 帧率 | 消息类型 | 发布者 | 用途 |
|---------|------|---------|--------|------|
| `/imu/data_raw` | **~100 Hz** | `sensor_msgs/msg/Imu` | `/rdk_imu_driver` | IMU 原始数据（加速度+角速度） |
| `/imu/temperature` | **~100 Hz** | `std_msgs/msg/Float32` | `/rdk_imu_driver` | IMU 温度监控 |

### 中频话题 (10-50 Hz)

| 话题名称 | 帧率 | 消息类型 | 发布者 | 用途 |
|---------|------|---------|--------|------|
| `/odom_combined` | **~30 Hz** ⬆️ | `nav_msgs/msg/Odometry` | `/ekf_filter_node` | ⭐ 融合里程计（推荐使用） |
| `/image` | **~14 fps** | `sensor_msgs/msg/CompressedImage` | `/hobot_usb_cam` | MJPEG 压缩图像流 |
| `/image/compressed` | **~14 fps** ⭐ | `sensor_msgs/msg/CompressedImage` | `/image_relay` | /image 的副本（兼容用） |
| `/hbmem_img` | **~14 fps** | `hbm_img_msgs/msg/HbmMsg1080P` | `/hobot_codec_decoder` | 共享内存图像（零拷贝） |
| `/odom` | **~20 Hz** | `nav_msgs/msg/Odometry` | `/origincar_base` | 轮式里程计（EKF 输入） |
| `/robotpose` | **~18 Hz** | `origincar_msg/msg/Data` | `/origincar_base` | 机器人位姿数据 |
| `/robotvel` | **~18 Hz** | `origincar_msg/msg/Data` | `/origincar_base` | 机器人速度数据 |
| `/PowerVoltage` | **~18 Hz** | `std_msgs/msg/Float32` | `/origincar_base` | 电池电压监控 |

### 低频话题 (<10 Hz)

| 话题名称 | 帧率 | 消息类型 | 发布者 | 用途 |
|---------|------|---------|--------|------|
| `/tf` | **~11 Hz** | `tf2_msgs/msg/TFMessage` | 多个节点 | 动态坐标变换 |
| `/joint_states` | **~10 Hz** | `sensor_msgs/msg/JointState` | `/joint_state_publisher` | 关节状态 |
| `/diagnostics` | **低频** | `diagnostic_msgs/msg/DiagnosticArray` | `/ekf_filter_node` | EKF 诊断信息 |

### 静态/事件驱动话题

| 话题名称 | 帧率 | 消息类型 | 发布者 | 用途 |
|---------|------|---------|--------|------|
| `/camera_info` | **单次** | `sensor_msgs/msg/CameraInfo` | `/hobot_usb_cam` | 相机标定信息 |
| `/robot_description` | **单次** | `std_msgs/msg/String` | `/robot_state_publisher` | URDF 描述（TRANSIENT_LOCAL） |
| `/client_count` | **事件驱动** | `std_msgs/msg/Int32` | `/rosbridge_websocket` | WebSocket 客户端数量 |
| `/connected_clients` | **事件驱动** | `rosbridge_msgs/msg/ConnectedClients` | `/rosbridge_websocket` | 连接的客户端列表 |

---

## 📈 性能分析

### 数据流延迟估算

```
IMU 数据采集:     BMI088 → /imu/data_raw        ~10ms (100Hz)
轮式里程计:       编码器 → /odom                ~50ms (20Hz)
EKF 融合:         /odom + /imu → /odom_combined  ~33ms (30Hz) ⬆️
图像采集:         USB Cam → /image              ~71ms (14fps) ⚠️
话题中继:         /image → /image/compressed    <1ms (零延迟)
硬件解码:         /image → /hbmem_img           ~5-10ms
```

### 系统负载评估

- **CPU 密集型**: 图像编解码（Hobot 硬件加速）
- **高频数据**: IMU (100Hz) - 对 CPU 影响小
- **中频数据**: 里程计融合 (30Hz) ⬆️ - 主要计算负载
- **低频数据**: 图像传输 (14fps) ⚠️ - 受硬件限制
- **网络带宽**: ROSBridge WebSocket (~1-3 Mbps，取决于图像订阅)

### 优化建议

1. **IMU 数据**: 100Hz 可能过高，如不需要可降低至 50Hz
2. **图像传输**: 当前 14fps 较低，可尝试调整摄像头参数提升至 20-25fps
3. **里程计融合**: 30Hz 是理想值，已优化完成 ✅
4. **TF 变换**: 11Hz 略低，可考虑提升至 20Hz 以提高平滑度
5. **图像压缩**: 当前 JPEG 质量适中，可根据带宽需求调整

---

**文档路径**: `/home/sunrise/RacingDev/dev_ws/src/origincar/ROS2_NODES_AND_TOPICS.md`  
**最后更新**: 2026-04-08
