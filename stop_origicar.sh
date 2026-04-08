#!/bin/bash
# ============================================
# Origicar ROS2 一键停止脚本（完整版）
# ============================================
# 功能：精准终止所有 ROS 节点和服务
# 包括：底盘节点、RDK IMU 驱动、EKF、摄像头、ROSBridge 等
# ============================================

echo "============================================"
echo "  🛑 正在停止所有服务..."
echo "============================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info_msg() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 停止所有相关进程（精准终止）
info_msg "清理 ROS2 节点..."
pkill -f "origincar_base" 2>/dev/null || true
pkill -f "hobot_usb_cam" 2>/dev/null || true
pkill -f "rosbridge_websocket" 2>/dev/null || true
pkill -f "hobot_codec" 2>/dev/null || true
pkill -f "robot_state_publisher" 2>/dev/null || true
pkill -f "joint_state_publisher" 2>/dev/null || true
pkill -f "static_transform_publisher" 2>/dev/null || true
pkill -f "websocket" 2>/dev/null || true
pkill -f "rosapi" 2>/dev/null || true
pkill -f "rdk_imu_driver" 2>/dev/null || true  # RDK IMU 驱动
pkill -f "ekf_node" 2>/dev/null || true
pkill -f "ekf_filter_node" 2>/dev/null || true
pkill -f "image_transport" 2>/dev/null || true

# 清理 ros2 launch 主进程
pkill -f "ros2 launch origincar" 2>/dev/null || true

sleep 2

# 检查是否还有残留进程
REMAINING=$(ps aux | grep -E "(origincar_base|hobot_usb_cam|rosbridge|ekf_node|ekf_filter|rdk_imu)" | grep -v grep | wc -l)

if [ $REMAINING -eq 0 ]; then
    echo "✅ 所有服务已完全停止"
else
    echo "⚠️  还有 $REMAINING 个进程未停止，尝试强制终止..."
    pkill -9 -f "origincar_base"
    pkill -9 -f "hobot_usb_cam"
    pkill -9 -f "rosbridge_websocket"
    pkill -9 -f "ekf_node"
    pkill -9 -f "ekf_filter_node"
    pkill -9 -f "rdk_imu_driver"
    sleep 1
fi

# 停止 ROS2 daemon
source /opt/ros/humble/setup.bash 2>/dev/null && ros2 daemon stop 2>/dev/null || true

echo ""
echo "============================================"
echo "  ✅ 清理完成"
echo "============================================"
echo ""
echo "📋 已停止的服务:"
echo "  - 🚗 车辆底盘节点 (origincar_base)"
echo "  - 🎛️ RDK IMU 驱动 & EKF 融合节点"
echo "  - 📹 USB 摄像头节点"
echo "  - 🔌 ROSBridge WebSocket 服务器"
echo ""
echo "💡 提示：如需重新启动，请执行：bash start_origicar.sh"
echo "     或使用高级选项：bash start_origicar.sh --akmcar"
echo "============================================"
