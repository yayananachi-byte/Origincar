import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Racing Image Collect Launch File
    
    功能：启动图像采集节点，用于收集训练数据集
    - 障碍物检测数据集（完整图像）
    - 赛道检测数据集（底部224行）
    """
    
    # 获取包路径
    pkg_dir = get_package_share_directory('racing_image_collect')
    
    # 声明启动参数
    launch_args = [
        DeclareLaunchArgument(
            'sub_img_topic',
            default_value='/image',
            description='订阅的图像话题名称（hobot_usb_cam 直接发布压缩格式）'
        ),
        DeclareLaunchArgument(
            'track_img_folder',
            default_value='img_collected/track',
            description='赛道检测数据集保存路径'
        ),
        DeclareLaunchArgument(
            'obstacle_img_folder',
            default_value='img_collected/obstacle',
            description='障碍物检测数据集保存路径'
        ),
        DeclareLaunchArgument(
            'fps',
            default_value='2.0',
            description='图片保存速率（帧/秒）'
        ),
    ]
    
    # 创建图像采集节点
    image_collect_node = Node(
        package='racing_image_collect',
        executable='racing_image_collect',
        name='racing_image_collect',
        output='screen',
        parameters=[
            {
                'sub_img_topic': LaunchConfiguration('sub_img_topic'),
                'track_img_folder': LaunchConfiguration('track_img_folder'),
                'obstacle_img_folder': LaunchConfiguration('obstacle_img_folder'),
                'fps': LaunchConfiguration('fps'),
            }
        ]
    )
    
    return LaunchDescription(launch_args + [
        image_collect_node
    ])
