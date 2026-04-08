#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BMI088 IMU Driver Node for RDK IMU Module
通过 I2C 接口读取 BMI088 传感器数据并发布为 ROS2 IMU 消息
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32
import smbus2
import time
import math


class BMI088Driver(Node):
    def __init__(self):
        super().__init__('bmi088_driver')
        
        # 参数声明
        self.declare_parameter('i2c_bus', 1)  # I2C 总线号
        self.declare_parameter('accel_address', 0x19)  # BMI088 加速度计地址
        self.declare_parameter('gyro_address', 0x69)   # BMI088 陀螺仪地址
        self.declare_parameter('publish_rate', 100.0)  # 发布频率 Hz
        self.declare_parameter('frame_id', 'imu_link')  # 坐标系
        
        # 获取参数
        self.i2c_bus = self.get_parameter('i2c_bus').get_parameter_value().integer_value
        self.accel_address = self.get_parameter('accel_address').get_parameter_value().integer_value
        self.gyro_address = self.get_parameter('gyro_address').get_parameter_value().integer_value
        self.publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        
        # 创建发布者
        self.imu_pub = self.create_publisher(Imu, '/imu/data_raw', 10)
        
        # 初始化 I2C
        try:
            self.bus = smbus2.SMBus(self.i2c_bus)
            self.get_logger().info(f'I2C bus {self.i2c_bus} initialized successfully')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize I2C bus: {e}')
            raise
        
        # BMI088 寄存器地址
        self.ACCEL_CHIP_ID = 0x00
        self.GYRO_CHIP_ID = 0x00
        self.EXPECTED_ACCEL_ID = 0x1E
        self.EXPECTED_GYRO_ID = 0x0F
        
        # 加速度计寄存器
        self.ACCEL_X_LSB = 0x12
        self.ACCEL_Y_LSB = 0x14
        self.ACCEL_Z_LSB = 0x16
        
        # 陀螺仪寄存器
        self.GYRO_X_LSB = 0x02
        self.GYRO_Y_LSB = 0x04
        self.GYRO_Z_LSB = 0x06
        
        # 量程配置
        self.accel_range = 24  # ±24g
        self.gyro_range = 2000  # ±2000 deg/s
        
        # 灵敏度
        self.accel_sensitivity = 16384.0  # LSB/g (for ±24g)
        self.gyro_sensitivity = 16.4      # LSB/deg/s (for ±2000 deg/s)
        
        # 重力加速度
        self.G = 9.80665
        
        # 初始化传感器
        if self.initialize_sensors():
            self.get_logger().info('BMI088 sensors initialized successfully')
        else:
            self.get_logger().error('Failed to initialize BMI088 sensors')
            raise RuntimeError('BMI088 initialization failed')
        
        # 创建定时器
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        self.get_logger().info(f'BMI088 driver node started, publishing at {self.publish_rate} Hz')
    
    def initialize_sensors(self):
        """初始化 BMI088 传感器"""
        try:
            # 读取芯片 ID
            accel_id = self.read_register(self.ACCEL_CHIP_ID, self.accel_address)
            gyro_id = self.read_register(self.GYRO_CHIP_ID, self.gyro_address)
            
            self.get_logger().info(f'Accelerometer ID: {hex(accel_id)} (Expected: {hex(self.EXPECTED_ACCEL_ID)})')
            self.get_logger().info(f'Gyroscope ID: {hex(gyro_id)} (Expected: {hex(self.EXPECTED_GYRO_ID)})')
            
            if accel_id != self.EXPECTED_ACCEL_ID or gyro_id != self.EXPECTED_GYRO_ID:
                self.get_logger().error('BMI088 chip ID mismatch!')
                return False
            
            # 初始化加速度计
            self.write_register(0x7D, 0x04, self.accel_address)  # 正常模式
            time.sleep(0.01)
            
            # 初始化陀螺仪
            self.write_register(0x15, 0x04, self.gyro_address)
            time.sleep(0.01)
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'Error initializing sensors: {e}')
            return False
    
    def read_register(self, register, address):
        """读取寄存器值"""
        try:
            data = self.bus.read_byte_data(address, register | 0x80)
            return data
        except Exception as e:
            self.get_logger().error(f'Error reading register {hex(register)}: {e}')
            return 0
    
    def write_register(self, register, value, address):
        """写入寄存器值"""
        try:
            self.bus.write_byte_data(address, register & 0x7F, value)
        except Exception as e:
            self.get_logger().error(f'Error writing register {hex(register)}: {e}')
    
    def read_accel_data(self):
        """读取加速度计数据"""
        try:
            # 读取 X 轴
            x_lsb = self.read_register(self.ACCEL_X_LSB, self.accel_address)
            x_msb = self.read_register(self.ACCEL_X_LSB + 1, self.accel_address)
            accel_x = (x_msb << 8) | x_lsb
            if accel_x > 32767:
                accel_x -= 65536
            
            # 读取 Y 轴
            y_lsb = self.read_register(self.ACCEL_Y_LSB, self.accel_address)
            y_msb = self.read_register(self.ACCEL_Y_LSB + 1, self.accel_address)
            accel_y = (y_msb << 8) | y_lsb
            if accel_y > 32767:
                accel_y -= 65536
            
            # 读取 Z 轴
            z_lsb = self.read_register(self.ACCEL_Z_LSB, self.accel_address)
            z_msb = self.read_register(self.ACCEL_Z_LSB + 1, self.accel_address)
            accel_z = (z_msb << 8) | z_lsb
            if accel_z > 32767:
                accel_z -= 65536
            
            # 转换为 m/s²
            accel_x_mss = (accel_x / self.accel_sensitivity) * self.G
            accel_y_mss = (accel_y / self.accel_sensitivity) * self.G
            accel_z_mss = (accel_z / self.accel_sensitivity) * self.G
            
            return accel_x_mss, accel_y_mss, accel_z_mss
            
        except Exception as e:
            self.get_logger().error(f'Error reading accel data: {e}')
            return 0.0, 0.0, 0.0
    
    def read_gyro_data(self):
        """读取陀螺仪数据"""
        try:
            # 读取 X 轴
            x_lsb = self.read_register(self.GYRO_X_LSB, self.gyro_address)
            x_msb = self.read_register(self.GYRO_X_LSB + 1, self.gyro_address)
            gyro_x = (x_msb << 8) | x_lsb
            if gyro_x > 32767:
                gyro_x -= 65536
            
            # 读取 Y 轴
            y_lsb = self.read_register(self.GYRO_Y_LSB, self.gyro_address)
            y_msb = self.read_register(self.GYRO_Y_LSB + 1, self.gyro_address)
            gyro_y = (y_msb << 8) | y_lsb
            if gyro_y > 32767:
                gyro_y -= 65536
            
            # 读取 Z 轴
            z_lsb = self.read_register(self.GYRO_Z_LSB, self.gyro_address)
            z_msb = self.read_register(self.GYRO_Z_LSB + 1, self.gyro_address)
            gyro_z = (z_msb << 8) | z_lsb
            if gyro_z > 32767:
                gyro_z -= 65536
            
            # 转换为 rad/s
            gyro_x_rads = math.radians(gyro_x / self.gyro_sensitivity)
            gyro_y_rads = math.radians(gyro_y / self.gyro_sensitivity)
            gyro_z_rads = math.radians(gyro_z / self.gyro_sensitivity)
            
            return gyro_x_rads, gyro_y_rads, gyro_z_rads
            
        except Exception as e:
            self.get_logger().error(f'Error reading gyro data: {e}')
            return 0.0, 0.0, 0.0
    
    def timer_callback(self):
        """定时器回调函数，发布 IMU 数据"""
        try:
            # 读取传感器数据
            accel_x, accel_y, accel_z = self.read_accel_data()
            gyro_x, gyro_y, gyro_z = self.read_gyro_data()
            
            # 创建 IMU 消息
            imu_msg = Imu()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = self.frame_id
            
            # 填充角速度数据
            imu_msg.angular_velocity.x = gyro_x
            imu_msg.angular_velocity.y = gyro_y
            imu_msg.angular_velocity.z = gyro_z
            imu_msg.angular_velocity_covariance = [
                0.01, 0.0, 0.0,
                0.0, 0.01, 0.0,
                0.0, 0.0, 0.01
            ]
            
            # 填充线加速度数据
            imu_msg.linear_acceleration.x = accel_x
            imu_msg.linear_acceleration.y = accel_y
            imu_msg.linear_acceleration.z = accel_z
            imu_msg.linear_acceleration_covariance = [
                0.01, 0.0, 0.0,
                0.0, 0.01, 0.0,
                0.0, 0.0, 0.01
            ]
            
            # 姿态四元数设为单位四元数（需要磁力计或算法解算）
            imu_msg.orientation.w = 1.0
            imu_msg.orientation_covariance = [
                1e6, 0.0, 0.0,
                0.0, 1e6, 0.0,
                0.0, 0.0, 1e-6
            ]
            
            # 发布消息
            self.imu_pub.publish(imu_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error in timer callback: {e}')


def main(args=None):
    rclpy.init(args=args)
    bmi088_node = BMI088Driver()
    
    try:
        rclpy.spin(bmi088_node)
    except KeyboardInterrupt:
        pass
    finally:
        bmi088_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
