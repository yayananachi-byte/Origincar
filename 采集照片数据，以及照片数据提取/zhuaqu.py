import os
import random
import shutil

# ===== 配置区 =====
source_folder = r"G:\qiepian\zhaopian"   # 原始图片路径
output_folder = r"G:\qiepian\zhuaqu"   # 输出路径（会自动创建）
num_samples = 120                         # 要随机抽取的数量
start_index = 209  # 自定义起始编号，比如从 120 开始（这边需要按需修改）

# ===== 创建输出文件夹 =====
os.makedirs(output_folder, exist_ok=True)

# ===== 获取所有 jpg/jpeg 图片 =====
all_images = [
    f for f in os.listdir(source_folder)
    if f.lower().endswith((".jpg", ".jpeg"))
]

print(f"总共有 {len(all_images)} 张图片")

# ===== 随机抽取 =====
if num_samples > len(all_images):
    raise ValueError("抽取数量超过图片总数！")

selected_images = random.sample(all_images, num_samples)

# ===== 拷贝并重新命名 =====
for i, fname in enumerate(selected_images, start=start_index):
    src_path = os.path.join(source_folder, fname)
    dst_path = os.path.join(output_folder, f"{i}.jpg")
    shutil.copy(src_path, dst_path)

print(f"已成功抽取 {num_samples} 张图片，编号从 {start_index} 到 {start_index + num_samples - 1}")
