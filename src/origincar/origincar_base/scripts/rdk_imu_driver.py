#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
name: rdk_imu_driver.py

description: RDK IMU Module ROS2 驱动节点
            将 RDK IMU 数据发布为标准的 sensor_msgs/Imu 消息

author: Modified from D-Robotics example
version: 1.0.0
date: 2026/04/08
"""

import sys
import os
import time
import threading
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32

# 添加 Py_RDK_IMU 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
              '../../../rdk_imu-library/Py_RDK_IMU'))

try:
    import rdkimu
except ImportError as e:
    print(f"Error importing rdkimu module: {e}")
    print("Please ensure rdkimu module is properly installed")
    sys.exit(1)


class RDKIMUDriver(Node):
    """RDK IMU 驱动节点"""
    
    def __init__(self):
        super().__init__('rdk_imu_driver')
        
        # 声明参数
        self.declare_parameter('publish_rate', 100.0)
        self.declare_parameter('frame_id', 'imu_link')
        self.declare_parameter('use_gpio', True)  # 是否使用 GPIO 控制 LED
        
        self.publish_rate = self.get_parameter('publish_rate').value
        self.frame_id = self.get_parameter('frame_id').value
        self.use_gpio = self.get_parameter('use_gpio').value
        
        # 创建发布者
        self.imu_pub = self.create_publisher(Imu, '/imu/data_raw', 10)
        self.temp_pub = self.create_publisher(Float32, '/imu/temperature', 10)
        
        # 初始化 IMU
        self.get_logger().info('Initializing RDK IMU...')
        if not self._init_imu():
            self.get_logger().error('Failed to initialize RDK IMU')
            return
        
        # 初始化 GPIO (可选)
        if self.use_gpio:
            try:
                self.imu_gpio = rdkimu.RDK_IMU_GPIO()
                self.get_logger().info('GPIO initialized successfully')
                # 闪烁提示
                self._blink_leds()
            except Exception as e:
                self.get_logger().warn(f'GPIO initialization failed: {e}')
                self.use_gpio = False
        
        # 读取板载温度
        if self.use_gpio:
            try:
                temp = self.imu_gpio.Get_Board_Temp()
                self.get_logger().info(f'Board temperature: {temp}°C')
            except:
                pass
        
        # 创建定时器
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self._timer_callback)
        
        self.get_logger().info(f'RDK IMU driver started (publish rate: {self.publish_rate} Hz)')
    
    def _init_imu(self):
        """初始化 IMU 硬件"""
        try:
            # 创建 IMU 实例
            self.imu = rdkimu.RDK_IMU()
            
            # 扫描设备
            ret, info = self.imu.Device_Scan()
            if not ret:
                self.get_logger().error('IMU device not found')
                return False
            
            self.get_logger().info(f'IMU device found: {info}')
            
            # 重置传感器
            self.imu.Accel_Reset()
            self.imu.Gyro_Reset()
            
            # 配置电源模式
            ret = self.imu.Set_Pwr_Mode(
                rdkimu.Accel_Pwr.pwr_on, 
                rdkimu.Gyro_Pwr.pwr_on
            )
            if not ret:
                self.get_logger().error('Failed to set power mode')
                return False
            
            # 配置加速度计
            ret = self.imu.Accel_Config()
            if not ret:
                self.get_logger().error('Failed to configure accelerometer')
                return False
            
            # 配置陀螺仪 (1000Hz ODR, 116Hz bandwidth)
            ret = self.imu.Gyro_Config(
                odr_bwp=rdkimu.Gyro_Odr_Bwp._1000hz_116hz
            )
            if not ret:
                self.get_logger().error('Failed to configure gyroscope')
                return False
            
            # 打印配置信息
            imu_info = self.imu.Get_IMU_Info()
            self.get_logger().info(f'IMU configuration: {imu_info}')
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'IMU initialization error: {e}')
            import traceback
            traceback.print_exc()
            return False
    
    def _blink_leds(self):
        """LED 闪烁提示"""
        try:
            colors = [
                {'led_r_st': rdkimu.GPIO_State._open, 'led_b_st': rdkimu.GPIO_State._close, 'led_g_st': rdkimu.GPIO_State._close},
                {'led_r_st': rdkimu.GPIO_State._close, 'led_b_st': rdkimu.GPIO_State._open, 'led_g_st': rdkimu.GPIO_State._close},
                {'led_r_st': rdkimu.GPIO_State._close, 'led_b_st': rdkimu.GPIO_State._close, 'led_g_st': rdkimu.GPIO_State._open},
            ]
            
            for color in colors:
                self.imu_gpio.GPIO_Ctrl(
                    bell_st=rdkimu.GPIO_State._open,
                    **color
                )
                time.sleep(0.1)
                self.imu_gpio.GPIO_Ctrl(
                    led_r_st=rdkimu.GPIO_State._close,
                    led_b_st=rdkimu.GPIO_State._close,
                    led_g_st=rdkimu.GPIO_State._close,
                    bell_st=rdkimu.GPIO_State._close
                )
                time.sleep(0.1)
        except Exception as e:
            self.get_logger().warn(f'LED blink failed: {e}')
    
    def _timer_callback(self):
        """定时发布 IMU 数据"""
        try:
            # 更新数据
            ret = self.imu.Data_Update()
            if not ret:
                self.get_logger().warn('IMU data update failed')
                return
            
            # 读取数据
            imu_data = self.imu.Data_Read()
            
            # 创建 IMU 消息
            imu_msg = Imu()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = self.frame_id
            
            # 加速度数据 (m/s²)
            accel = imu_data.get('Accel', {})
            imu_msg.linear_acceleration.x = accel.get('x', 0.0) * 9.80665  # g -> m/s²
            imu_msg.linear_acceleration.y = accel.get('y', 0.0) * 9.80665
            imu_msg.linear_acceleration.z = accel.get('z', 0.0) * 9.80665
            
            # 角速度数据 (rad/s)
            angvel = imu_data.get('AngVel', {})
            imu_msg.angular_velocity.x = angvel.get('x', 0.0) * 0.0174533  # deg/s -> rad/s
            imu_msg.angular_velocity.y = angvel.get('y', 0.0) * 0.0174533
            imu_msg.angular_velocity.z = angvel.get('z', 0.0) * 0.0174533
            
            # 协方差矩阵 (需要根据实际传感器性能调整)
            # 加速度协方差
            imu_msg.linear_acceleration_covariance[0] = 0.01  # x
            imu_msg.linear_acceleration_covariance[4] = 0.01  # y
            imu_msg.linear_acceleration_covariance[8] = 0.01  # z
            
            # 角速度协方差
            imu_msg.angular_velocity_covariance[0] = 0.001  # x
            imu_msg.angular_velocity_covariance[4] = 0.001  # y
            imu_msg.angular_velocity_covariance[8] = 0.001  # z
            
            # 发布 IMU 消息
            self.imu_pub.publish(imu_msg)
            
            # 发布温度数据
            temp = imu_data.get('Temp', 0.0)
            temp_msg = Float32()
            temp_msg.data = float(temp)
            self.temp_pub.publish(temp_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error publishing IMU data: {e}')
            import traceback
            traceback.print_exc()
    
    def destroy_node(self):
        """清理资源"""
        if self.use_gpio:
            try:
                # 关闭所有 LED
                self.imu_gpio.GPIO_Ctrl(
                    led_r_st=rdkimu.GPIO_State._close,
                    led_b_st=rdkimu.GPIO_State._close,
                    led_g_st=rdkimu.GPIO_State._close,
                    bell_st=rdkimu.GPIO_State._close
                )
            except:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = RDKIMUDriver()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Fatal error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
