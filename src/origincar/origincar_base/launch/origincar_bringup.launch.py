import os
from pathlib import Path
import launch
from launch.actions import SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import PushRosNamespace
import launch_ros.actions
from launch.conditions import UnlessCondition, IfCondition

def generate_launch_description():
    # Get the launch directory
    bringup_dir = get_package_share_directory('origincar_base')
    launch_dir = os.path.join(bringup_dir, 'launch')
    
    # IMU 类型选择参数：'bmi088' 或 'mpu6050' (默认)
    use_bmi088_arg = DeclareLaunchArgument(
        'use_bmi088',
        default_value='false',
        description='Use BMI088 IMU if true, otherwise use MPU6050 IMU (from serial port, default)'
    )
    use_bmi088 = LaunchConfiguration('use_bmi088')
    
    # 根据 IMU 类型选择不同的 EKF 配置
    ekf_config_bmi088 = Path(get_package_share_directory('origincar_base'), 'config', 'ekf_bmi088.yaml')
    ekf_config_mpu6050 = Path(get_package_share_directory('origincar_base'), 'config', 'ekf_mpu6050.yaml')
    imu_config = Path(get_package_share_directory('origincar_base'), 'config', 'imu.yaml')

    
    carto_slam = LaunchConfiguration('carto_slam', default='false')
    carto_slam_dec = DeclareLaunchArgument('carto_slam',default_value='false')
            
    origincar_base = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, 'base_serial.launch.py')),
            launch_arguments={'akmcar': 'false'}.items(),
    )

    choose_car = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, 'robot_mode_description.launch.py')),
    )

    
    base_to_link = launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_link',
            arguments=['0.41', '0.12', '0','0', '0','0','base_footprint','base_link'],
    )
    base_to_gyro = launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_gyro',
            arguments=['0', '0', '0','0', '0','0','base_footprint','gyro_link'],
    )
    
    link_to_laser = launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='link_to_laser',
            arguments=['0', '0', '0','0', '0','0','base_link','laser'],
    )

    # BMI088 IMU 驱动节点（条件启动）
    bmi088_driver_node = launch_ros.actions.Node(
        condition=IfCondition(use_bmi088),
        package='origincar_base',
        executable='bmi088_imu_driver.py',
        name='bmi088_driver',
        output='screen',
        parameters=[{
            'i2c_bus': 1,
            'accel_address': '0x19',
            'gyro_address': '0x69',
            'publish_rate': 100.0,
            'frame_id': 'imu_link'
        }]
    )
    
    # MPU6050 使用 IMU 滤波器（条件启动）
    imu_filter_node = launch_ros.actions.Node(
        condition=UnlessCondition(use_bmi088),
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        parameters=[imu_config]
    )
    
    # EKF 融合节点 - 根据 IMU 类型选择不同配置
    # 直接输出到 /odom_combined，支持通过 /set_pose 话题重置位姿
    robot_ekf_bmi088 = launch_ros.actions.Node(
        condition=IfCondition(use_bmi088),
        package='robot_localization',
        executable='ekf_node',
        parameters=[ekf_config_bmi088],
        remappings=[("odometry/filtered", "odom_combined")]
    )
    
    robot_ekf_mpu6050 = launch_ros.actions.Node(
        condition=UnlessCondition(use_bmi088),
        package='robot_localization',
        executable='ekf_node',
        parameters=[ekf_config_mpu6050],
        remappings=[("odometry/filtered", "odom_combined")]
    )
                              
    joint_state_publisher_node = launch_ros.actions.Node(
            package='joint_state_publisher', 
            executable='joint_state_publisher', 
            name='joint_state_publisher',
    )

    ld = LaunchDescription()

    ld.add_action(carto_slam_dec)
    ld.add_action(use_bmi088_arg)
    ld.add_action(origincar_base)
    ld.add_action(base_to_link)
    ld.add_action(base_to_gyro)
    ld.add_action(joint_state_publisher_node)
    ld.add_action(choose_car)
    ld.add_action(bmi088_driver_node)
    ld.add_action(imu_filter_node)
    ld.add_action(robot_ekf_bmi088)
    ld.add_action(robot_ekf_mpu6050)

    return ld

