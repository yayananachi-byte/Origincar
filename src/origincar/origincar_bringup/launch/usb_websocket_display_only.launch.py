import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import TextSubstitution, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python import get_package_share_directory, get_package_prefix

def generate_launch_description():
    # Declare launch arguments
    launch_args = [
        DeclareLaunchArgument('device', default_value='/dev/video0', description='usb camera device'),
    ]

    # USB camera node - publishes /image (MJPEG)
    # 配置: 640x480 @ 25fps
    usb_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(get_package_share_directory('hobot_usb_cam') + '/launch/hobot_usb_cam.launch.py'),
        launch_arguments={
            'usb_image_width': '640', 
            'usb_image_height': '480',
            'usb_framerate': '25',  # 设置帧率为 25fps
            'usb_video_device': LaunchConfiguration('device')
        }.items()
    )

    # NV12 codec node - converts /image to shared memory /hbmem_img
    # 用于 AI 推理等需要 NV12 格式的场景
    nv12_codec_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(get_package_share_directory('hobot_codec') + '/launch/hobot_codec_decode.launch.py'),
        launch_arguments={
            'codec_in_mode': 'ros', 
            'codec_out_mode': 'shared_mem',
            'codec_sub_topic': '/image', 
            'codec_pub_topic': '/hbmem_img',
            'codec_input_framerate': '25'  # 与摄像头帧率一致
        }.items()
    )

    # JPEG codec node (hobot_codec_encoder) - DISABLED
    # 已禁用：不需要重新编码发布 /image 话题
    # 现在只有 hobot_usb_cam 发布 /image
    # jpeg_codec_node = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(get_package_share_directory('hobot_codec') + '/launch/hobot_codec_encode.launch.py'),
    #     launch_arguments={
    #         'codec_in_mode': 'shared_mem', 
    #         'codec_out_mode': 'ros',
    #         'codec_sub_topic': '/hbmem_img', 
    #         'codec_pub_topic': '/image',
    #         'codec_in_format': 'nv12',
    #         'codec_out_format': 'jpeg'
    #     }.items()
    # )

    # Web display node - visualization only (no DNN inference)
    # 设置 log_level 为 error 以抑制 AI 数据缺失的警告
    web_node = Node(
        package='websocket',
        executable='websocket',
        output='screen',
        parameters=[
            {'image_topic': '/image'},
            {'image_type': 'mjpeg'},
            {'only_show_image': True},  # 布尔类型
            {'smart_topic': ''}  # 空字符串，不订阅任何 AI 话题
        ],
        arguments=['--ros-args', '--log-level', 'error']  # 只显示错误，忽略警告
    )

    return LaunchDescription(launch_args + [
        usb_node,
        nv12_codec_node,
        # jpeg_codec_node,  # 已禁用
        web_node
    ])
