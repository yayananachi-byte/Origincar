# Testing Inertial Nav - 惯性导航测试功能包

## 📋 功能说明

这是一个基于 EKF 融合里程计的惯性导航测试功能包，实现以下功能：

1. **自动原点标定**：以小车上电时的位姿为坐标原点 (0, 0, 0)
2. **多航点导航**：在预设的多个坐标点之间自动运动
3. **PID 精确控制**：使用双 PID 控制器实现位置和角度的精确控制
4. **相对坐标系**：所有坐标均相对于启动原点，便于理解和调试

## 🏗️ 系统架构

```
┌─────────────────────┐
│  EKF Fusion Node    │  ← 订阅 /imu/data_raw 和 /odom
│  (robot_localization)│     输出融合后的里程计
└──────────┬──────────┘
           │ /odom_combined
           ↓
┌─────────────────────┐
│ Inertial Nav        │  ← 本功能包
│ Controller          │     • 接收融合里程计
│                     │     • 计算相对位置
│                     │     • PID 控制算法
└──────────┬──────────┘
           │ /cmd_vel
           ↓
┌─────────────────────┐
│  Robot Base         │  ← 执行运动指令
│  (origincar_base)   │
└─────────────────────┘
```

## 📦 文件结构

```
testing_inertial_nav/
├── CMakeLists.txt                  # 编译配置
├── package.xml                     # 包描述
├── include/
│   └── inertial_nav_controller.hpp # 头文件
├── src/
│   └── inertial_nav_controller.cpp # 核心实现
├── config/
│   └── params.yaml                 # 参数配置
├── launch/
│   └── inertial_nav.launch.py      # 启动文件
└── README.md                       # 本文档
```

## 🚀 快速开始

### 1. 编译功能包

```bash
cd ~/RacingDev/dev_ws
colcon build --packages-select testing_inertial_nav
source install/setup.bash
```

### 2. 启动基础系统（EKF 融合）

确保已经启动了包含 EKF 融合的完整系统：

```bash
# 方式1：使用现有的启动脚本
./start_origicar.sh

# 方式2：手动启动 EKF
ros2 launch origincar_base ekf_rdk_imu.launch.py
```

验证 EKF 正常工作：
```bash
ros2 topic echo /odom_combined
```

### 3. 启动惯性导航控制器

```bash
ros2 launch testing_inertial_nav inertial_nav.launch.py
```

### 4. 观察运行状态

```bash
# 查看日志输出
# 终端会显示当前位置、目标航点、距离等信息

# 可视化（可选）
rviz2
# 添加 Odometry 显示 /odom_combined
# 添加 TF 显示坐标系
```

## ⚙️ 配置说明

### 修改航点路径

编辑 `src/inertial_nav_controller.cpp` 第 136-143 行：

```cpp
// 定义航点（相对于原点）
// 格式: Waypoint(x, y, yaw)
waypoints_.push_back(Waypoint(1.0, 0.0, 0.0));      // 航点1: 向前1米
waypoints_.push_back(Waypoint(1.0, 1.0, M_PI/2));   // 航点2: 向左1米
waypoints_.push_back(Waypoint(0.0, 1.0, M_PI));     // 航点3: 向后1米
waypoints_.push_back(Waypoint(0.0, 0.0, -M_PI/2));  // 航点4: 返回原点
```

**坐标说明：**
- `x`: 前后方向（前进为正）
- `y`: 左右方向（左转为正）
- `yaw`: 目标朝向（弧度，逆时针为正）

**示例路径：**

```cpp
// 正方形路径（边长1米）
waypoints_.push_back(Waypoint(1.0, 0.0, 0.0));
waypoints_.push_back(Waypoint(1.0, 1.0, M_PI/2));
waypoints_.push_back(Waypoint(0.0, 1.0, M_PI));
waypoints_.push_back(Waypoint(0.0, 0.0, -M_PI/2));

// 直线往返
waypoints_.push_back(Waypoint(2.0, 0.0, 0.0));
waypoints_.push_back(Waypoint(0.0, 0.0, M_PI));

// 圆形近似（8个点）
for (int i = 0; i < 8; i++) {
    double angle = i * M_PI / 4;
    double x = cos(angle);
    double y = sin(angle);
    waypoints_.push_back(Waypoint(x, y, angle + M_PI/2));
}
```

### 调整控制参数

编辑 `config/params.yaml`：

```yaml
# 到达判定阈值
position_tolerance: 0.05    # 位置误差容忍度（米）
angle_tolerance: 0.05       # 角度误差容忍度（弧度）

# 速度限制
max_linear_speed: 0.5       # 最大线速度（m/s）
max_angular_speed: 1.0      # 最大角速度（rad/s）

# PID 参数 - 线性运动
linear_kp: 0.8              # 比例增益（增大→响应更快，但可能震荡）
linear_ki: 0.0              # 积分增益（消除稳态误差）
linear_kd: 0.1              # 微分增益（抑制震荡）

# PID 参数 - 角度运动
angular_kp: 2.0             # 通常比线性 kp 大
angular_ki: 0.0
angular_kd: 0.3
```

**调参建议：**
1. 先调整 `kp`，使系统能快速响应
2. 如果出现震荡，增加 `kd`
3. 如果有稳态误差，增加 `ki`
4. 降低 `max_linear_speed` 可以提高精度

## 📊 监控与调试

### 查看实时位置

```bash
# 方法1：查看节点日志
ros2 run testing_inertial_nav inertial_nav_controller

# 方法2：订阅里程计话题
ros2 topic echo /odom_combined | grep position

# 方法3：使用 tf2_echo
ros2 run tf2_ros tf2_echo odom_combined base_footprint
```

### 绘制轨迹

```bash
# 记录里程计数据
ros2 bag record /odom_combined -o nav_test_bag

# 回放分析
ros2 bag play nav_test_bag
```

### 常见问题

**问题1：小车不动**
- 检查 `/odom_combined` 是否有数据：`ros2 topic hz /odom_combined`
- 检查 `/cmd_vel` 是否发布：`ros2 topic echo /cmd_vel`
- 确认 EKF 已启动并正常运行

**问题2：导航精度差**
- 减小 `position_tolerance`（如改为 0.03）
- 降低 `max_linear_speed`（如改为 0.3）
- 调整 PID 参数，增加 `kd` 抑制震荡

**问题3：原点漂移**
- 确保启动时小车静止
- 检查 IMU 校准是否正常
- 验证 EKF 配置正确

**问题4：无法到达航点**
- 增大 `position_tolerance`
- 检查地面摩擦力是否过大
- 确认电池电量充足

## 🔧 高级用法

### 动态修改航点（运行时）

可以通过 ROS2 服务或参数服务器实现动态航点更新（需要额外开发）。

### 添加避障功能

在 `navigate_to_waypoint()` 函数中添加障碍物检测：

```cpp
// 伪代码示例
if (obstacle_detected && distance_to_obstacle < safe_distance) {
    stop_robot();
    wait_for_obstacle_clearance();
}
```

### 保存和加载路径

可以将航点保存到 YAML 文件：

```yaml
waypoints:
  - {x: 1.0, y: 0.0, yaw: 0.0}
  - {x: 1.0, y: 1.0, yaw: 1.57}
  - {x: 0.0, y: 1.0, yaw: 3.14}
```

然后在代码中读取。

## 📝 技术细节

### 坐标系定义

```
         y (左)
         ↑
         |
         |
origin --+--→ x (前)
(0,0,0)
```

- **原点**：上电时刻小车的位姿
- **X轴**：小车前进方向
- **Y轴**：小车左侧方向
- **Yaw**：逆时针旋转为正

### PID 控制原理

**线性运动 PID：**
```
error = 目标距离 - 当前距离
output = kp * error + ki * ∫error + kd * d(error)/dt
```

**角度运动 PID：**
```
error = 目标角度 - 当前角度
output = kp * error + ki * ∫error + kd * d(error)/dt
```

### 航点切换逻辑

1. 计算到当前航点的距离
2. 如果距离 < tolerance，认为到达
3. 停止 0.5 秒
4. 切换到下一个航点
5. 重置 PID 积分项

## 📚 参考资料

- [ROS2 Navigation](https://navigation.ros.org/)
- [robot_localization](http://docs.ros.org/en/noetic/api/robot_localization/html/)
- [PID Control Theory](https://en.wikipedia.org/wiki/PID_controller)

## 👨‍💻 作者

Created for RacingDev project by sunrise

## 📄 许可证

Apache-2.0
