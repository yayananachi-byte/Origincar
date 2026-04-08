# 惯性导航测试快速指南

## 🚀 5分钟快速开始

### 前提条件
确保已经编译并安装了功能包：
```bash
cd ~/RacingDev/dev_ws
colcon build --packages-select testing_inertial_nav
source install/setup.bash
```

### 步骤1: 启动基础系统

```bash
# 方式A: 使用完整启动脚本（推荐）
./start_origicar.sh

# 方式B: 仅启动 EKF 融合
ros2 launch origincar_base ekf_rdk_imu.launch.py
```

**验证 EKF 正常运行：**
```bash
ros2 topic hz /odom_combined
# 应该看到约 30 Hz 的数据输出
```

### 步骤2: 启动惯性导航

```bash
# 方式A: 使用启动脚本
ros2 launch testing_inertial_nav inertial_nav.launch.py

# 方式B: 使用便捷脚本
cd src/racing/testing_inertial_nav/scripts
./start_test.sh
```

### 步骤3: 观察运行

终端会显示类似输出：
```
======================================
Inertial Navigation Controller Started
======================================
Loaded 4 waypoints
  Waypoint 1: (1.00, 0.00, 0.00 rad)
  Waypoint 2: (1.00, 1.00, 1.57 rad)
  ...
Waiting for odometry data...
Origin will be set on first odometry message
======================================
Origin initialized at:
  Global: (0.123, -0.456, 0.789)
  Relative: (0.0, 0.0, 0.0)
Starting waypoint navigation...
======================================
>>> Moving to waypoint 1/4
Navigating to (1.00, 0.00) | Dist: 0.987 m | Angle err: 0.012 rad
...
✓ Reached waypoint (1.00, 0.00)
>>> Moving to waypoint 2/4
...
```

## 📊 实时监控

### 查看小车位置
```bash
# 方法1: TF 变换
ros2 run tf2_ros tf2_echo odom_combined base_footprint

# 方法2: 里程计话题
ros2 topic echo /odom_combined | grep -A 3 "position:"

# 方法3: Rviz2 可视化
rviz2
# 添加 Displays:
#   - Odometry (/odom_combined)
#   - TF
#   - RobotModel
```

### 查看控制指令
```bash
ros2 topic echo /cmd_vel
```

### 绘制轨迹（高级）
```bash
# 记录数据
ros2 bag record /odom_combined -o test_run_$(date +%Y%m%d_%H%M%S)

# 停止后分析
ros2 bag info <bag_file>
```

## 🔧 常见问题排查

### ❌ 问题1: 小车不动

**检查清单：**
```bash
# 1. 检查 EKF 是否运行
ros2 topic list | grep odom_combined

# 2. 检查是否有里程计数据
ros2 topic echo /odom_combined --once

# 3. 检查 cmd_vel 是否发布
ros2 topic echo /cmd_vel

# 4. 检查节点日志
ros2 node info /inertial_nav_controller
```

**可能原因：**
- EKF 未启动 → 启动 `ekf_rdk_imu.launch.py`
- 话题名称不匹配 → 检查 remapping
- 小车被急停 → 检查底盘状态

### ❌ 问题2: 导航精度差

**症状：** 无法准确到达目标点，偏差较大

**解决方案：**
1. **降低速度** (`config/params.yaml`)
   ```yaml
   max_linear_speed: 0.3    # 从 0.5 降到 0.3
   max_angular_speed: 0.8   # 从 1.0 降到 0.8
   ```

2. **调整 PID**
   ```yaml
   linear_kp: 1.0           # 增大响应
   linear_kd: 0.2           # 抑制震荡
   angular_kp: 2.5          # 增强转向
   ```

3. **减小容差**
   ```yaml
   position_tolerance: 0.03  # 从 5cm 降到 3cm
   ```

4. **重新校准 IMU**
   ```bash
   # 静止小车，观察 IMU 漂移
   ros2 topic echo /imu/data_raw
   ```

### ❌ 问题3: 原点漂移

**症状：** 启动后坐标系持续偏移

**解决方案：**
1. 确保启动时小车完全静止
2. 检查地面是否水平
3. 验证 EKF 配置中的 IMU 参数
4. 增加 `process_noise_covariance` 中对角线元素

### ❌ 问题4: 震荡或超调

**症状：** 在目标点附近来回摆动

**解决方案：**
```yaml
# 增加微分项
linear_kd: 0.3
angular_kd: 0.5

# 或降低比例项
linear_kp: 0.5
angular_kp: 1.5
```

## 🎯 修改测试路径

### 编辑代码
打开 `src/inertial_nav_controller.cpp`，找到第 136-143 行：

```cpp
// 当前默认路径（正方形）
waypoints_.push_back(Waypoint(1.0, 0.0, 0.0));
waypoints_.push_back(Waypoint(1.0, 1.0, M_PI/2));
waypoints_.push_back(Waypoint(0.0, 1.0, M_PI));
waypoints_.push_back(Waypoint(0.0, 0.0, -M_PI/2));
```

### 替换为其他路径

参考 `config/waypoint_examples.txt` 中的示例，例如改为直线往返：

```cpp
waypoints_.clear();  // 清空现有航点
waypoints_.push_back(Waypoint(2.0, 0.0, 0.0));
waypoints_.push_back(Waypoint(0.0, 0.0, M_PI));
```

### 重新编译
```bash
colcon build --packages-select testing_inertial_nav
source install/setup.bash
```

## 📈 性能优化建议

### 提高精度
1. **降低速度** - 速度与精度成反比
2. **增加采样率** - `control_frequency: 30.0`
3. **使用更小的容差** - `position_tolerance: 0.02`
4. **优化 PID** - 通过实验找到最佳参数

### 提高稳定性
1. **确保良好地面** - 避免打滑
2. **充足电量** - 低电量影响电机响应
3. **IMU 预热** - 启动后等待 10-30 秒
4. **减少干扰** - 远离强磁场源

### 调试技巧
```bash
# 启用 DEBUG 日志
ros2 run testing_inertial_nav inertial_nav_controller --ros-args --log-level debug

# 只查看特定级别
ros2 run testing_inertial_nav inertial_nav_controller --ros-args --log-level info
```

## 🧪 测试场景建议

### 场景1: 基础功能验证
- 路径：直线往返 1 米
- 目的：验证基本运动和控制
- 预期：误差 < 5cm

### 场景2: 转向精度测试
- 路径：正方形（1m × 1m）
- 目的：测试 90° 转向精度
- 预期：角度误差 < 5°

### 场景3: 长距离导航
- 路径：直线 3-5 米
- 目的：测试累积误差
- 预期：误差 < 10cm

### 场景4: 复杂路径
- 路径：圆形或螺旋
- 目的：测试连续转向
- 预期：轨迹平滑，无明显震荡

## 📝 记录测试结果

建议创建测试记录表：

| 测试日期 | 路径类型 | 距离 | 最大速度 | 位置误差 | 角度误差 | 备注 |
|---------|---------|------|---------|---------|---------|------|
| 2026-04-08 | 正方形 | 4m | 0.5 m/s | 3.2 cm | 2.1° | 表现良好 |
| ... | ... | ... | ... | ... | ... | ... |

## 🆘 获取帮助

如果遇到问题：

1. **查看完整日志**
   ```bash
   ros2 log show
   ```

2. **检查依赖**
   ```bash
   ros2 pkg dependencies testing_inertial_nav
   ```

3. **验证安装**
   ```bash
   ros2 pkg executables testing_inertial_nav
   # 应该显示: testing_inertial_nav inertial_nav_controller
   ```

4. **联系支持**
   - 查看 README.md 详细文档
   - 检查 GitHub Issues
   - 提供完整日志和错误信息

---

**祝测试顺利！** 🎉
