# -*- coding: utf-8 -*-
import cv2
import os

def video_to_frames(video_path, save_dir, step=1):
    """
    视频转图片
    :param video_path: 输入视频路径
    :param save_dir: 输出图片文件夹
    :param step: 每隔多少帧保存一张（默认1，表示每帧都保存）
    """
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return

    frame_id = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % step == 0:
            save_path = os.path.join(save_dir, f"frame_{frame_id:05d}.jpg")
            cv2.imwrite(save_path, frame)
            saved += 1

        frame_id += 1

    cap.release()
    print(f" 完成: 共读取 {frame_id} 帧，保存 {saved} 张图片到 {save_dir}")


if __name__ == "__main__":
    # 这里改成你自己视频的路径
    video_path = r"G:\qiepian\mv\001.avi "    # 输入视频文件位置
    save_dir   = r"G:\qiepian\zhaopian"       # 输出图片文件夹切片下来的照片
    step       = 5                         # 每隔5帧保存一张

    video_to_frames(video_path, save_dir, step)
