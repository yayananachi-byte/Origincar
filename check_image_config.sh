#!/bin/bash
# 验证图像配置脚本

source /opt/ros/humble/setup.bash
cd /home/sunrise/RacingDev/dev_ws
source install/setup.bash

echo "=========================================="
echo "  图像配置验证"
echo "=========================================="
echo ""

echo "1. 检查运行的节点..."
ros2 node list | grep -E "hobot|codec|websocket"
echo ""

echo "2. 检查 /image 话题的发布者..."
ros2 topic info /image 2>&1 | grep -A 10 "Publisher count"
echo ""

echo "3. 测量 /image 话题帧率（5秒）..."
timeout 5 ros2 topic hz /image 2>&1 | tail -3
echo ""

echo "4. 检查 /hbmem_img 话题..."
ros2 topic info /hbmem_img 2>&1 | head -15
echo ""

echo "5. 测量 /hbmem_img 话题帧率（5秒）..."
timeout 5 ros2 topic hz /hbmem_img 2>&1 | tail -3
echo ""

echo "=========================================="
echo "  验证完成"
echo "=========================================="
