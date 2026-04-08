import os
from pathlib import Path
import launch
from launch.actions import SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace
import launch_ros.actions

def generate_launch_description():
    # Get the launch directory
    bringup_dir = get_package_share_directory('origincar_base')
    launch_dir = os.path.join(bringup_dir, 'launch')
    
    # EKF 配置文件路径 - 仅使用 RDK IMU
    ekf_config_rdk = Path(get_package_share_directory('origincar_base'), 'config', 'ekf_rdk_imu.yaml')
    
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

    # RDK IMU 驱动节点 - 唯一的 IMU 数据源
    rdk_imu_driver_node = launch_ros.actions.Node(
        package='origincar_base',
        executable='rdk_imu_driver.py',
        name='rdk_imu_driver',
        output='screen',
        parameters=[{
            'publish_rate': 100.0,
            'frame_id': 'imu_link',
            'use_gpio': True
        }]
    )
    
    # EKF 融合节点 - 使用 RDK IMU 配置
    # 融合轮式里程计和 RDK IMU，输出到 /odom_combined
    robot_ekf_rdk = launch_ros.actions.Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        parameters=[ekf_config_rdk],
        remappings=[("odometry/filtered", "odom_combined")],
        output='screen'
    )
                              
    joint_state_publisher_node = launch_ros.actions.Node(
            package='joint_state_publisher', 
            executable='joint_state_publisher', 
            name='joint_state_publisher',
    )

    ld = LaunchDescription()

    ld.add_action(carto_slam_dec)
    ld.add_action(origincar_base)
    ld.add_action(base_to_link)
    ld.add_action(base_to_gyro)
    ld.add_action(joint_state_publisher_node)
    ld.add_action(choose_car)
    ld.add_action(rdk_imu_driver_node)
    ld.add_action(robot_ekf_rdk)

    return ld
