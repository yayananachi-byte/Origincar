# Copyright (c) 2022，Horizon Robotics.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# import rclpy
# from rclpy.node import Node
# from cv_bridge import CvBridge
# import cv2 as cv
# import uuid
# import os
# import numpy as np
# import datetime
# import time
# from sensor_msgs.msg import Image


# class ImageSubscriber(Node):

#   def __init__(self):
#     super().__init__('ImageSubscriber')
#     # 创建sub节点，订阅image_raw话题
#     self.declare_parameter("fps",2.0)
#     self.declare_parameter("sub_img_topic","/image")
#     self.declare_parameter("track_img_folder","track_image1")
#     self.declare_parameter("obstacle_img_folder","obstacle_image1")
#     self.subscription = self.create_subscription(
#       Image,
#       self.get_parameter('sub_img_topic').get_parameter_value().string_value,
#       self.listener_callback,
#       1)
#     # 创建CvBridge实例
#     self.bridge = CvBridge()
#     self.uuid = -1
#     self.line_follow_image = np.zeros((640, 224, 3))
#     self.detection_image = np.zeros((640, 480, 3))
#     self.start_time = time.time()
#     self.time_diff_threshold = 1 / self.get_parameter('fps').get_parameter_value().double_value

#     self.line_follow_image_folder = self.get_parameter('track_img_folder').get_parameter_value().string_value
#     self.detection_image_folder = self.get_parameter('obstacle_img_folder').get_parameter_value().string_value
#     if not os.path.exists(self.line_follow_image_folder):
#       os.makedirs(self.line_follow_image_folder)
#     if not os.path.exists(self.detection_image_folder):
#       os.makedirs(self.detection_image_folder)
#     self.subscription
  


#   def listener_callback(self, msg):
#     end_time = time.time()
#     time_diff = end_time - self.start_time
#     if time_diff > self.time_diff_threshold:
#       self.start_time = end_time
#       self.detection_image = self.bridge.imgmsg_to_cv2(msg)
#       self.line_follow_image = self.detection_image[255:479,:,:].copy()
#       self.uuid = uuid.uuid1()
#       cv.imwrite(os.path.join(self.line_follow_image_folder, str(self.uuid) + '.jpg'), self.line_follow_image)
#       cv.imwrite(os.path.join(self.detection_image_folder, str(self.uuid) + '.jpg'), self.detection_image)
#       print("Save"+ str(self.uuid) + ".jpg")



# def main(args=None):
#   rclpy.init(args=args)
#   image_subscriber = ImageSubscriber()
#   rclpy.spin(image_subscriber)
#   image_subscriber.destroy_node()
#   rclpy.shutdown()

# if __name__ == '__main__':
#   main()

# import rclpy
# from rclpy.node import Node
# from cv_bridge import CvBridge, CvBridgeError
# import cv2 as cv
# import uuid
# import os
# import numpy as np
# import datetime
# import time
# from sensor_msgs.msg import CompressedImage  # 修改这里，导入CompressedImage

# class ImageSubscriber(Node):

#     def __init__(self):
#         super().__init__('ImageSubscriber')
#         # 创建sub节点，订阅image_raw话题
#         self.declare_parameter("fps", 2.0)
#         self.declare_parameter("sub_img_topic", "/image/compressed")  # 订阅compressed图像话题
#         self.declare_parameter("track_img_folder", "track_image1")
#         self.declare_parameter("obstacle_img_folder", "obstacle_image1")
#         # 创建订阅，订阅/image/compressed话题上的CompressedImage类型的消息
#         self.subscription = self.create_subscription(
#             CompressedImage,  # 修改这里，订阅CompressedImage类型
#             self.get_parameter('sub_img_topic').get_parameter_value().string_value,
#             self.listener_callback,
#             1)
#         self.bridge = CvBridge()
#         self.uuid = -1
#         self.line_follow_image = np.zeros((640, 224, 3))
#         self.detection_image = np.zeros((640, 480, 3))
#         self.start_time = time.time()
#         self.time_diff_threshold = 1 / self.get_parameter('fps').get_parameter_value().double_value

#         self.line_follow_image_folder = self.get_parameter('track_img_folder').get_parameter_value().string_value
#         self.detection_image_folder = self.get_parameter('obstacle_img_folder').get_parameter_value().string_value
#         if not os.path.exists(self.line_follow_image_folder):
#             os.makedirs(self.line_follow_image_folder)
#         if not os.path.exists(self.detection_image_folder):
#             os.makedirs(self.detection_image_folder)

#     def listener_callback(self, msg):
#         end_time = time.time()
#         time_diff = end_time - self.start_time
#         if time_diff > self.time_diff_threshold:
#             self.start_time = end_time
#             try:
#                 # 将压缩图像消息转换为OpenCV图像
#                 self.detection_image = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")  # 假设压缩图像是bgr8编码
#             except CvBridgeError as e:
#                 self.get_logger().error(f"CvBridge error: {e}")
#                 return

#             # 假设压缩图像的分辨率是640x480，根据需要截取图像
#             self.line_follow_image = self.detection_image[160:384, 0:640].copy()  # 修改这里的截取范围
#             self.uuid = uuid.uuid1()
#             cv.imwrite(os.path.join(self.line_follow_image_folder, str(self.uuid) + '.jpg'), self.line_follow_image)
#             cv.imwrite(os.path.join(self.detection_image_folder, str(self.uuid) + '.jpg'), self.detection_image)
#             print("Saved image with UUID: " + str(self.uuid))

# def main(args=None):
#     rclpy.init(args=args)
#     image_subscriber = ImageSubscriber()
#     rclpy.spin(image_subscriber)
#     image_subscriber.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge, CvBridgeError
import cv2 as cv
import uuid
import os
import numpy as np
import datetime
import time
from sensor_msgs.msg import CompressedImage  # 修改这里，导入CompressedImage

class ImageSubscriber(Node):
    # ... 其他代码保持不变 ...

    def __init__(self):
        super().__init__('ImageSubscriber')
        # 初始化图像计数器
        self.image_count = 0
        self.declare_parameter("fps", 2.0)
        self.declare_parameter("sub_img_topic", "/image")  # hobot_usb_cam 直接发布压缩格式到 /image
        self.declare_parameter("track_img_folder", "img_collected/track")
        self.declare_parameter("obstacle_img_folder", "img_collected/obstacle")
        
        # 创建带时间戳的根文件夹
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_folder = f"img_collected/recording_{timestamp}"
        
        # 创建子文件夹
        track_subfolder = os.path.join(self.base_folder, "track")
        obstacle_subfolder = os.path.join(self.base_folder, "obstacle")
        
        if not os.path.exists(track_subfolder):
            os.makedirs(track_subfolder)
        if not os.path.exists(obstacle_subfolder):
            os.makedirs(obstacle_subfolder)
        
        self.get_logger().info(f"📁 创建录制文件夹: {self.base_folder}")
        self.get_logger().info(f"   - 赛道数据: {track_subfolder}")
        self.get_logger().info(f"   - 障碍物数据: {obstacle_subfolder}")
        
        # 创建订阅
        self.subscription = self.create_subscription(
            CompressedImage,
            self.get_parameter('sub_img_topic').get_parameter_value().string_value,
            self.listener_callback,
            1)
        self.bridge = CvBridge()
        self.uuid = -1
        self.line_follow_image = np.zeros((640, 224, 3))
        self.detection_image = np.zeros((640, 480, 3))
        self.start_time = time.time()
        self.time_diff_threshold = 1 / self.get_parameter('fps').get_parameter_value().double_value

        # 使用带时间戳的路径
        self.line_follow_image_folder = track_subfolder
        self.detection_image_folder = obstacle_subfolder

    def listener_callback(self, msg):
        end_time = time.time()
        time_diff = end_time - self.start_time
        if time_diff > self.time_diff_threshold:
            self.start_time = end_time
            try:
                # 将压缩图像消息转换为OpenCV图像
                # self.detection_image = self.bridge.compressed_imgmsg_to_cv2(msg, "bgr8")
                self.detection_image = self.bridge.compressed_imgmsg_to_cv2(msg)
            except CvBridgeError as e:
                self.get_logger().error(f"CvBridge error: {e}")
                return

            # 截取图像
            # self.line_follow_image = self.detection_image[160:384, 0:640].copy()
            self.line_follow_image = self.detection_image[255:479,:,:].copy()
            # 增加图像计数器
            self.image_count += 1
            # 格式化序列号，例如："0001", "0002", ...
            serial_number = f"{self.image_count:04d}"  # 4位数字，不足前面补零
            # 生成文件名
            line_follow_image_filename = f"line_follow_{serial_number}.jpg"
            detection_image_filename = f"detection_{serial_number}.jpg"

            # 保存图像
            cv.imwrite(os.path.join(self.line_follow_image_folder, line_follow_image_filename), self.line_follow_image)
            cv.imwrite(os.path.join(self.detection_image_folder, detection_image_filename), self.detection_image)
            print(f"Saved image with name: {line_follow_image_filename} and {detection_image_filename}")

def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()
    rclpy.spin(image_subscriber)
    image_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
