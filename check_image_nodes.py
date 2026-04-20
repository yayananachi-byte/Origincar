#!/usr/bin/env python3
"""检查图像相关节点和话题"""

import subprocess
import time

def run_command(cmd):
    """运行命令并返回输出"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

print("=" * 80)
print("📊 Origicar 系统 - 图像节点和话题检查")
print("=" * 80)
print()

# 1. 检查运行的进程
print("1️⃣  图像相关进程:")
print("-" * 80)
ps_output = run_command("ps aux | grep -E '(hobot|websocket|codec)' | grep -v grep | head -10")
if ps_output:
    for line in ps_output.split('\n'):
        if line.strip():
            # 提取进程名
            parts = line.split()
            if len(parts) > 10:
                pid = parts[1]
                cmd = ' '.join(parts[10:])
                print(f"  PID {pid:6s}: {cmd[:70]}")
else:
    print("  ⚠️  未找到相关进程")

print()

# 2. 检查 ROS2 节点
print("2️⃣  ROS2 节点列表:")
print("-" * 80)
nodes_output = run_command("source /opt/ros/humble/setup.bash && ros2 node list 2>/dev/null")
if nodes_output:
    nodes = [n.strip() for n in nodes_output.split('\n') if n.strip()]
    image_related = []
    for node in nodes:
        if any(kw in node.lower() for kw in ['hobot', 'usb', 'cam', 'codec', 'websocket', 'relay']):
            image_related.append(node)
    
    if image_related:
        for node in image_related:
            print(f"  ✅ {node}")
    else:
        print("  ℹ️  所有节点:")
        for node in nodes[:15]:  # 只显示前15个
            print(f"    - {node}")
else:
    print("  ⚠️  无法获取节点列表")

print()

# 3. 检查图像话题
print("3️⃣  图像相关话题:")
print("-" * 80)
topics_output = run_command("source /opt/ros/humble/setup.bash && ros2 topic list 2>/dev/null")
if topics_output:
    topics = [t.strip() for t in topics_output.split('\n') if t.strip()]
    image_topics = [t for t in topics if 'image' in t.lower()]
    
    if image_topics:
        for topic in image_topics:
            # 获取话题类型
            type_output = run_command(f"source /opt/ros/humble/setup.bash && ros2 topic type {topic} 2>/dev/null")
            print(f"  ✅ {topic:40s} -> {type_output}")
    else:
        print("  ⚠️  未找到图像相关话题")
        
        # 显示所有话题
        print("\n  ℹ️  所有可用话题:")
        for topic in topics[:20]:
            print(f"    - {topic}")
else:
    print("  ⚠️  无法获取话题列表")

print()

# 4. 检查主要图像话题的频率
print("4️⃣  图像话题频率测试 (采样3秒):")
print("-" * 80)
test_topics = ['/image', '/hbmem_img', '/image/compressed']

for topic in test_topics:
    print(f"\n  测试 {topic}...")
    hz_output = run_command(f"source /opt/ros/humble/setup.bash && timeout 3 ros2 topic hz {topic} 2>&1 | grep -i 'average'")
    if hz_output:
        print(f"    {hz_output}")
    else:
        print(f"    ⚠️  无数据或话题不存在")

print()
print("=" * 80)
print("✅ 检查完成")
print("=" * 80)
