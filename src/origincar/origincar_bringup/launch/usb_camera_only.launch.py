import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import TextSubstitution, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python import get_package_share_directory

def generate_launch_description():
    # Declare launch arguments
    launch_args = [
        DeclareLaunchArgument('device', default_value='/dev/video0', description='usb camera device'),
        DeclareLaunchArgument('image_width', default_value='640', description='image width'),
        DeclareLaunchArgument('image_height', default_value='480', description='image height'),
    ]

    # USB camera node - 读取摄像头数据并发布到 /image 话题
    usb_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(get_package_share_directory('hobot_usb_cam') + '/launch/hobot_usb_cam.launch.py'),
        launch_arguments={
            'usb_image_width': LaunchConfiguration('image_width'), 
            'usb_image_height': LaunchConfiguration('image_height'),
            'usb_video_device': LaunchConfiguration('device')
        }.items()
    )

    # NV12 codec node - converts to shared memory /hbmem_img
    nv12_codec_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(get_package_share_directory('hobot_codec') + '/launch/hobot_codec_decode.launch.py'),
        launch_arguments={
            'codec_in_mode': 'ros', 
            'codec_out_mode': 'shared_mem',
            'codec_sub_topic': '/image', 
            'codec_pub_topic': '/hbmem_img'
        }.items()
    )

    # JPEG codec node - encodes for web display
    jpeg_codec_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(get_package_share_directory('hobot_codec') + '/launch/hobot_codec_encode.launch.py'),
        launch_arguments={
            'codec_in_mode': 'shared_mem', 
            'codec_out_mode': 'ros',
            'codec_sub_topic': '/hbmem_img', 
            'codec_pub_topic': '/image',
            'codec_in_format': 'nv12',
            'codec_out_format': 'jpeg'
        }.items()
    )

    return LaunchDescription(launch_args + [
        usb_node,
        nv12_codec_node,
        jpeg_codec_node
    ])
