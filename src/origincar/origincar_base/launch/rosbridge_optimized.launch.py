"""
ROSBridge WebSocket 启动文件（优化版）
解决 nav_msgs/Odometry 序列化问题
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{
                'port': 9090,
                'address': '',
                'fragment_timeout': 600,
                'delay_between_messages': 0.0,
                'max_message_size': 10000000,  # 10MB
                'buffer_size': 1000000,
                'call_services_in_new_thread': True,
                'send_action_goals_in_new_thread': True,
                'default_call_service_timeout': 5.0,
                'use_compression': False,
                'unregister_timeout': 10.0,
                'authenticate': False,
            }],
        ),
        Node(
            package='rosapi',
            executable='rosapi_node',
            name='rosapi',
            output='screen',
        ),
    ])
