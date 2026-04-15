# -*- coding: utf-8 -*-
import cv2
import datetime
import time

def measure_fps(cap, sample_frames=60):
    """jianceFPS"""
    frames = 0
    start = time.time()
    while frames < sample_frames:
        ret, _ = cap.read()
        if not ret:
            break
        frames += 1
    elapsed = time.time() - start
    return frames / elapsed if elapsed > 0 else 0

def main():
    device_index = 0
    WIDTH  = 640
    HEIGHT = 480
    REQUEST_FPS = 21   #帧率设置
    OUTPUT = datetime.datetime.now().strftime("output_%Y%m%d_%H%M%S.avi")

    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        print("NOOPEN")
        return

    # 请求 MJPG 格式 + 分辨率
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, REQUEST_FPS)

    # 读取一帧确认相机正常
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Not obtained")
        cap.release()
        return
    h, w = frame.shape[:2]

    # 测量实际 FPS
    real_fps = measure_fps(cap, sample_frames=60)
    print(f"Requested FPS: {REQUEST_FPS}, Measured FPS: {real_fps:.2f}")

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(OUTPUT, fourcc, real_fps, (w, h))
    if not out.isOpened():
        print("VideoWriter failed to open")
        cap.release()
        return

    print(f"Recording {w}x{h} @ {real_fps:.2f} fps -> {OUTPUT}")
    print("Press Ctrl+C or press 'q' to stop...")

    frames = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            out.write(frame)
            frames += 1

            # 实时预览窗口
            preview = cv2.resize(frame, (160, 120))
            #缩小预览窗口
            cv2.imshow("Recording", preview)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Stopped by user (q)")
                break

    except KeyboardInterrupt:
        print("Stopped by user (Ctrl+C)")

    # 释放资源
    out.release()
    cap.release()
    cv2.destroyAllWindows()

    elapsed = time.time() - start_time
    avg_fps = frames / elapsed if elapsed > 0 else 0
    print(f"Done. Wrote {frames} frames in {elapsed:.2f}s, avg {avg_fps:.2f} fps")
    print(f"Saved: {OUTPUT}")

if __name__ == "__main__":
    main()
