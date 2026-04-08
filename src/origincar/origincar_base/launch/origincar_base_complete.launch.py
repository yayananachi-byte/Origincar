#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Origincar Base Complete Launch File
支持 BMI088 和 MPU6050 两种 IMU 切换
默认使用 BMI088 IMU
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = 'origincar_base'
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    
    # IMU 类型选择参数：'bmi088' 或 'mpu6050' (默认)
    use_bmi088 = LaunchConfiguration('use_bmi088', default='false')
    
    # 其他参数
    akmcar = LaunchConfiguration('akmcar', default='false')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # I2C 参数（仅 BMI088 需要）
    i2c_bus = LaunchConfiguration('i2c_bus', default='1')
    
    # 声明参数
    declare_use_bmi088 = DeclareLaunchArgument(
        'use_bmi088',
        default_value='false',
        description='Use BMI088 IMU if true, otherwise use MPU6050 IMU (from serial port, default)'
    )
    
    declare_akmcar = DeclareLaunchArgument(
        'akmcar',
        default_value='false',
        description='Use Ackermann steering mode if true'
    )
    
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true'
    )
    
    declare_i2c_bus = DeclareLaunchArgument(
        'i2c_bus',
        default_value='1',
        description='I2C bus number for BMI088 (default: 1 for RDK X5)'
    )
    
    # BMI088 IMU 驱动节点（条件启动）
    bmi088_imu_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch/bmi088_imu.launch.py')
        ),
        launch_arguments={
            'i2c_bus': i2c_bus,
            'use_sim_time': use_sim_time
        }.items(),
        condition=IfCondition(use_bmi088)
    )
    
    # EKF 融合节点（根据 IMU 类型选择不同配置）
    ekf_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch/ekf.launch.py')
        ),
        launch_arguments={
            'use_bmi088': use_bmi088,
            'use_sim_time': use_sim_time
        }.items()
    )
    
    # 底盘串口通信节点
    base_serial_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch/base_serial.launch.py')
        ),
        launch_arguments={
            'akmcar': akmcar
        }.items()
    )
    
    return LaunchDescription([
        declare_use_bmi088,
        declare_akmcar,
        declare_use_sim_time,
        declare_i2c_bus,
        bmi088_imu_node,
        ekf_node,
        base_serial_node
    ])
