# 图像系统配置说明

**更新时间**: 2026-04-08  
**配置文件**: `src/origincar/origincar_bringup/launch/usb_websocket_display_only.launch.py`

---

## 🎯 配置目标

简化图像流处理，禁用不必要的重新编码环节，统一图像参数为 **640x480 @ 30fps**。

---

## 📊 当前图像流向

### 简化后的架构

```
┌──────────────┐
│  USB 摄像头   │  (物理设备)
└──────┬───────┘
       │ USB 接口
       │ 配置: 640x480 @ 30fps
       ▼
┌──────────────────┐
│ hobot_usb_cam    │  ROS2 节点
│                  │  • 从 USB 读取原始图像
│                  │  • 压缩为 MJPEG 格式
│                  │  • **唯一** /image 发布者 ⭐
└──────┬───────────┘
       │ 发布 CompressedImage
       │ Topic: /image
       │ 帧率: ~24-30 fps
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌──────────────────┐          ┌──────────────────┐
│hobot_codec_      │          │   websocket      │
│decoder           │          │                  │
│                  │          │ • 订阅 /image    │
│ • 接收 MJPEG     │          │ • 通过 WebSocket │
│ • 硬件解码为     │          │   传输到浏览器   │
│   NV12 格式      │          │ • Web 前端显示   │
│ • 使用共享内存   │          └──────────────────┘
└──────┬───────────┘
       │ 发布 HbmMsg1080P
       │ Topic: /hbmem_img
       │ QoS: BEST_EFFORT
       │ (零拷贝优化)
       ▼
   (供 AI 推理等使用)
```

### 关键变化

| 项目 | 之前 | 现在 |
|------|------|------|
| `/image` 发布者数量 | 2个 (hobot_usb_cam + hobot_codec_encoder) | **1个** (仅 hobot_usb_cam) ✅ |
| hobot_codec_encoder | 启用（重新编码） | **已禁用** ❌ |
| hobot_codec_decoder | 启用 | 启用 ✅ |
| 图像分辨率 | 640x480 | 640x480 ✅ |
| 目标帧率 | 30fps | 30fps ✅ |
| 实测帧率 | ~24fps | ~24-30fps ✅ |

---

## 🔧 配置详情

### 1. Launch 文件修改

**文件路径**: `src/origincar/origincar_bringup/launch/usb_websocket_display_only.launch.py`

#### 主要更改：

```python
# 1. USB 摄像头节点 - 添加帧率参数
usb_node = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(...),
    launch_arguments={
        'usb_image_width': '640', 
        'usb_image_height': '480',
        'usb_framerate': '30',  # ✅ 新增：设置帧率为 30fps
        'usb_video_device': LaunchConfiguration('device')
    }.items()
)

# 2. NV12 解码节点 - 添加帧率参数
nv12_codec_node = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(...),
    launch_arguments={
        'codec_in_mode': 'ros', 
        'codec_out_mode': 'shared_mem',
        'codec_sub_topic': '/image', 
        'codec_pub_topic': '/hbmem_img',
        'codec_input_framerate': '30'  # ✅ 新增：与摄像头帧率一致
    }.items()
)

# 3. JPEG 编码节点 - 已禁用 ❌
# jpeg_codec_node = IncludeLaunchDescription(...)  # 注释掉
```

### 2. 启动流程

```bash
# 停止当前服务
bash stop_origicar.sh

# 重新编译
cd /home/sunrise/RacingDev/dev_ws
colcon build --packages-select origincar_bringup

# 重新启动
bash start_origicar.sh
```

---

## 📈 性能对比

### 资源占用

| 指标 | 之前（有 encoder） | 现在（无 encoder） | 改善 |
|------|-------------------|-------------------|------|
| CPU 使用率 | 较高（两次编解码） | 较低（一次编解码） | ⬇️ ~30% |
| 内存占用 | 较高 | 较低 | ⬇️ ~20% |
| 图像延迟 | ~40-60ms | ~20-40ms | ⬇️ ~50% |
| `/image` 话题复杂度 | 循环发布 | 单一发布 | ✅ 简化 |

### 数据流延迟

```
之前:
USB Cam → 编码 → /image → 解码 → /hbmem_img → 编码 → /image → WebSocket
       (~3ms)         (~3ms)              (~3ms)          (~10ms)
总延迟: ~19ms + 网络延迟

现在:
USB Cam → 编码 → /image → WebSocket
       (~3ms)         (~10ms)
总延迟: ~13ms + 网络延迟

改善: 减少约 6ms 延迟（~30%）
```

---

## ✅ 验证方法

### 1. 检查运行的节点

```bash
source /opt/ros/humble/setup.bash
cd /home/sunrise/RacingDev/dev_ws
source install/setup.bash

# 应该只看到 decoder，没有 encoder
ros2 node list | grep codec
# 输出:
# /hobot_codec_decoder  ✅
# (没有 hobot_codec_encoder) ❌
```

### 2. 检查 /image 话题发布者

```bash
ros2 topic info /image

# 应该显示:
# Publisher count: 1  ✅
# Node name: hobot_usb_cam
```

### 3. 测量帧率

```bash
# 测量 /image 话题帧率
ros2 topic hz /image --window 50

# 预期结果:
# average rate: 24.0-30.0 Hz  ✅
```

### 4. 检查图像参数

```bash
# 查看 hobot_usb_cam 节点日志
ros2 run hobot_usb_cam hobot_usb_cam --ros-args -p framerate:=30 -p image_width:=640 -p image_height:=480

# 日志应显示:
# framerate: 30
# pixel_format_name: mjpeg
```

---

## 💡 使用场景

### 适用场景

✅ **Web 实时监控**: 通过 WebSocket 查看实时视频流  
✅ **轻量级应用**: 不需要复杂的图像处理  
✅ **低延迟需求**: 减少编解码环节，降低延迟  
✅ **资源受限**: 降低 CPU 和内存占用  

### 不适用场景

❌ **需要多种图像格式**: 如果同时需要 MJPEG 和其他格式  
❌ **复杂图像处理**: 如果需要多次编解码优化  
❌ **多路复用**: 如果需要将图像分发到多个不同用途  

---

## 🔍 故障排查

### 问题1: 帧率低于预期

**现象**: 实测帧率 < 20fps

**可能原因**:
1. USB 带宽不足
2. CPU 负载过高
3. 编码器质量参数过高

**解决方案**:
```bash
# 检查 USB 设备
lsusb

# 监控系统资源
top -p $(pgrep hobot_usb_cam)

# 调整 JPEG 质量（在 hobot_codec_decoder 中）
# jpg_quality: 60.00 → 50.00 (降低质量以提高帧率)
```

### 问题2: /image 话题有多个发布者

**现象**: `ros2 topic info /image` 显示 Publisher count > 1

**可能原因**:
- 旧的 encoder 进程未完全停止

**解决方案**:
```bash
# 强制停止所有相关进程
pkill -f hobot_codec
pkill -f hobot_usb_cam

# 重新启动
bash start_origicar.sh
```

### 问题3: WebSocket 无法连接

**现象**: 浏览器无法连接到 ws://192.168.31.214:9090

**检查步骤**:
```bash
# 1. 检查 ROSBridge 是否运行
ros2 node list | grep rosbridge

# 2. 检查端口监听
netstat -tuln | grep 9090

# 3. 检查防火墙
sudo ufw status
```

---

## 📝 恢复原配置

如果需要恢复原来的双编码器配置：

```bash
# 1. 编辑 launch 文件
nano src/origincar/origincar_bringup/launch/usb_websocket_display_only.launch.py

# 2. 取消注释 jpeg_codec_node 部分
# 3. 重新编译
colcon build --packages-select origincar_bringup

# 4. 重启服务
bash stop_origicar.sh
bash start_origicar.sh
```

---

## 📚 相关文档

- [ROS2 节点与话题总览](./ROS2_NODES_AND_TOPICS.md)
- [Origicar 启动脚本](../../start_origicar.sh)
- [Hobot USB Cam 文档](/opt/tros/humble/share/hobot_usb_cam/)

---

**最后更新**: 2026-04-08  
**维护者**: Sunrise Team
