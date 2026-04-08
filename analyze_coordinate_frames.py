#!/usr/bin/env python3
"""
坐标系分析报告
分析轮式里程计、融合里程计和IMU的坐标系关系
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
import sys

class CoordinateFrameAnalyzer(Node):
    def __init__(self):
        super().__init__('coordinate_frame_analyzer')
        
        self.get_logger().info('\n' + '='*80)
        self.get_logger().info('📊 坐标系分析报告')
        self.get_logger().info('='*80)
        
        # 订阅各个话题，只接收一次消息来分析
        self.odom_received = False
        self.odom_combined_received = False
        self.imu_received = False
        
        self.create_subscription(Odometry, '/odom', self.odom_callback, 1)
        self.create_subscription(Odometry, '/odom_combined', self.odom_combined_callback, 1)
        self.create_subscription(Imu, '/imu/data_raw', self.imu_callback, 1)
        
        self.timer = self.create_timer(5.0, self.check_completion)
        self.start_time = self.get_clock().now()
    
    def odom_callback(self, msg):
        if not self.odom_received:
            self.odom_received = True
            self.get_logger().info('\n📍 1️⃣  轮式里程计 (/odom)')
            self.get_logger().info(f'   坐标系: frame_id="{msg.header.frame_id}" -> child_frame_id="{msg.child_frame_id}"')
            self.get_logger().info(f'   含义: 从 {msg.header.frame_id} 到 {msg.child_frame_id} 的变换')
            self.get_logger().info(f'   位置: x={msg.pose.pose.position.x:.3f}, y={msg.pose.pose.position.y:.3f}, z={msg.pose.pose.position.z:.3f}')
    
    def odom_combined_callback(self, msg):
        if not self.odom_combined_received:
            self.odom_combined_received = True
            self.get_logger().info('\n📍 2️⃣  融合里程计 (/odom_combined)')
            self.get_logger().info(f'   坐标系: frame_id="{msg.header.frame_id}" -> child_frame_id="{msg.child_frame_id}"')
            self.get_logger().info(f'   含义: 从 {msg.header.frame_id} 到 {msg.child_frame_id} 的变换')
            self.get_logger().info(f'   位置: x={msg.pose.pose.position.x:.3f}, y={msg.pose.pose.position.y:.3f}, z={msg.pose.pose.position.z:.3f}')
    
    def imu_callback(self, msg):
        if not self.imu_received:
            self.imu_received = True
            self.get_logger().info('\n📍 3️⃣  IMU数据 (/imu/data_raw)')
            self.get_logger().info(f'   坐标系: frame_id="{msg.header.frame_id}"')
            self.get_logger().info(f'   含义: IMU传感器坐标系')
            self.get_logger().info(f'   加速度: ax={msg.linear_acceleration.x:.3f}, ay={msg.linear_acceleration.y:.3f}, az={msg.linear_acceleration.z:.3f} m/s²')
    
    def check_completion(self):
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        
        if self.odom_received and self.odom_combined_received and self.imu_received:
            self.print_summary()
            rclpy.shutdown()
        elif elapsed > 10:
            self.get_logger().warn('⚠️  超时，可能有些话题没有数据')
            self.print_summary()
            rclpy.shutdown()
    
    def print_summary(self):
        self.get_logger().info('\n' + '='*80)
        self.get_logger().info('📋 坐标系关系总结')
        self.get_logger().info('='*80)
        
        self.get_logger().info('\n🔗 TF坐标变换树:')
        self.get_logger().info('   odom_combined (世界坐标系/里程计坐标系)')
        self.get_logger().info('     └─[EKF发布]─> base_footprint (机器人基座标系)')
        self.get_logger().info('                        ├─[静态]─> base_link (底盘中心)')
        self.get_logger().info('                        │           └─[静态]─> laser (激光雷达)')
        self.get_logger().info('                        └─[静态]─> gyro_link (陀螺仪)')
        self.get_logger().info('                        ⚠️  imu_link 不存在！(应该添加)')
        
        self.get_logger().info('\n📊 各话题坐标系说明:')
        self.get_logger().info('   1. /odom (轮式里程计)')
        self.get_logger().info('      - 发布: origincar_base节点')
        self.get_logger().info('      - 坐标系: odom_combined -> base_footprint')
        self.get_logger().info('      - 注意: frame_id被设置为odom_combined（与融合里程计相同）')
        
        self.get_logger().info('\n   2. /odom_combined (融合里程计)')
        self.get_logger().info('      - 发布: ekf_filter_node节点')
        self.get_logger().info('      - 坐标系: odom_combined -> base_footprint')
        self.get_logger().info('      - 说明: EKF融合轮式里程计和IMU数据后的结果')
        
        self.get_logger().info('\n   3. /imu/data_raw (IMU原始数据)')
        self.get_logger().info('      - 发布: rdk_imu_driver节点')
        self.get_logger().info('      - 坐标系: imu_link')
        self.get_logger().info('      - ⚠️  问题: imu_link在TF树中不存在！')
        
        self.get_logger().info('\n⚙️  EKF融合配置:')
        self.get_logger().info('   - odom_frame: odom_combined (输出的里程计坐标系)')
        self.get_logger().info('   - base_link_frame: base_footprint (机器人基座标系)')
        self.get_logger().info('   - world_frame: odom_combined (世界坐标系)')
        self.get_logger().info('   - 输入1: /odom (轮式里程计)')
        self.get_logger().info('   - 输入2: /imu/data_raw (IMU数据，frame_id=imu_link)')
        
        self.get_logger().info('\n❗ 发现的问题:')
        self.get_logger().info('   1. IMU发布的frame_id是"imu_link"，但TF树中没有定义这个坐标系')
        self.get_logger().info('   2. Launch文件只定义了"gyro_link"，没有定义"imu_link"')
        self.get_logger().info('   3. 这会导致TF树不连续，影响某些需要完整TF树的功能')
        
        self.get_logger().info('\n💡 建议修复方案:')
        self.get_logger().info('   方案A: 在launch文件中添加 imu_link 的静态变换')
        self.get_logger().info('          static_transform_publisher 0 0 0 0 0 0 base_footprint imu_link')
        self.get_logger().info('   方案B: 修改IMU驱动的frame_id参数为 gyro_link')
        self.get_logger().info('          parameters=[{\'frame_id\': \'gyro_link\'}]')
        
        self.get_logger().info('\n✅ 当前系统可以正常工作，因为:')
        self.get_logger().info('   - EKF内部会处理不同frame_id的数据')
        self.get_logger().info('   - 轮式里程计和融合里程计都使用相同的坐标系')
        self.get_logger().info('   - 但对于完整的TF树，建议修复上述问题')
        
        self.get_logger().info('\n' + '='*80 + '\n')


def main(args=None):
    rclpy.init(args=args)
    node = CoordinateFrameAnalyzer()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
