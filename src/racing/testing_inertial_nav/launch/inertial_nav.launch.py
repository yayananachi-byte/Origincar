import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package directory
    pkg_dir = get_package_share_directory('testing_inertial_nav')
    
    # Load configuration
    config_file = os.path.join(pkg_dir, 'config', 'params.yaml')
    
    # Create inertial navigation controller node
    inertial_nav_node = Node(
        package='testing_inertial_nav',
        executable='inertial_nav_controller',
        name='inertial_nav_controller',
        output='screen',
        parameters=[config_file],
        remappings=[
            ('/odom_combined', '/odom_combined'),  # EKF fused odometry
            ('/cmd_vel', '/cmd_vel'),              # Velocity command
        ]
    )
    
    return LaunchDescription([
        inertial_nav_node
    ])
