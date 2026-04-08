#!/usr/bin/python3

import os
import launch
import launch_ros
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    
    package_name = 'origincar_base'
    ld =  launch.LaunchDescription()
    pkg_share = launch_ros.substitutions.FindPackageShare(package=package_name).find(package_name) 
    
    # IMU 类型选择：'bmi088' 或 'mpu6050' (默认)
    use_bmi088 = LaunchConfiguration('use_bmi088', default='false')
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    # 根据 IMU 类型选择配置文件
    bmi088_config_path = os.path.join(pkg_share, 'config/ekf_bmi088.yaml')
    mpu6050_config_path = os.path.join(pkg_share, 'config/ekf_mpu6050.yaml')
    
    # Start robot localization using an Extended Kalman filter
    robot_localization_node = Node(
      package='robot_localization',
      executable='ekf_node',
      name='ekf_filter_node',
      output='screen',
      remappings=[("odometry/filtered", "odom_combined")],
      parameters=[
          {'use_sim_time': use_sim_time}
      ])
    
    # 条件加载不同的 EKF 配置
    bmi088_ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        remappings=[("odometry/filtered", "odom_combined")],
        parameters=[
            bmi088_config_path,
            {'use_sim_time': use_sim_time}
        ],
        condition=IfCondition(use_bmi088)
    )
    
    mpu6050_ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        remappings=[("odometry/filtered", "odom_combined")],
        parameters=[
            mpu6050_config_path,
            {'use_sim_time': use_sim_time}
        ],
        condition=UnlessCondition(use_bmi088)
    )

    ld.add_action(launch.actions.DeclareLaunchArgument(
        name='use_bmi088', 
        default_value='true',
        description='Use BMI088 IMU if true, otherwise use MPU6050 IMU'
    ))
    ld.add_action(launch.actions.DeclareLaunchArgument(
        name='use_sim_time', 
        default_value='false',
        description='Flag to disable use_sim_time'
    ))
    
    ld.add_action(bmi088_ekf_node)
    ld.add_action(mpu6050_ekf_node)
    return ld
