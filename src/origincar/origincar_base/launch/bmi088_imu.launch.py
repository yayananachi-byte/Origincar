#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BMI088 IMU Driver Launch File
启动 BMI088 IMU 驱动节点
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = 'origincar_base'
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    
    # 参数声明
    i2c_bus_arg = DeclareLaunchArgument(
        'i2c_bus',
        default_value='1',
        description='I2C bus number (default: 1 for RDK X5)'
    )
    
    accel_address_arg = DeclareLaunchArgument(
        'accel_address',
        default_value='0x19',
        description='BMI088 accelerometer I2C address'
    )
    
    gyro_address_arg = DeclareLaunchArgument(
        'gyro_address',
        default_value='0x69',
        description='BMI088 gyroscope I2C address'
    )
    
    publish_rate_arg = DeclareLaunchArgument(
        'publish_rate',
        default_value='100.0',
        description='IMU data publish rate in Hz'
    )
    
    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='imu_link',
        description='Frame ID for IMU messages'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true'
    )
    
    # BMI088 驱动节点
    bmi088_driver_node = Node(
        package='origincar_base',
        executable='bmi088_imu_driver.py',
        name='bmi088_driver',
        output='screen',
        parameters=[{
            'i2c_bus': LaunchConfiguration('i2c_bus'),
            'accel_address': LaunchConfiguration('accel_address'),
            'gyro_address': LaunchConfiguration('gyro_address'),
            'publish_rate': LaunchConfiguration('publish_rate'),
            'frame_id': LaunchConfiguration('frame_id'),
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )
    
    return LaunchDescription([
        i2c_bus_arg,
        accel_address_arg,
        gyro_address_arg,
        publish_rate_arg,
        frame_id_arg,
        use_sim_time_arg,
        bmi088_driver_node
    ])
