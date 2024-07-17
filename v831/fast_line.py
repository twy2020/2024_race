# -*- coding: utf-8 -*-
import cv2
import numpy as np

# 初始化参数
THRESHOLD = 100  # 灰度图像的阈值
roi = [(0, 100, 32, 40), (32, 100, 32, 40), (64, 100, 32, 40), (96, 100, 32, 40),
       (128, 100, 32, 40), (160, 100, 32, 40), (192, 100, 32, 40), (224, 100, 32, 40),
       (256, 100, 32, 40), (288, 100, 32, 40)]  # 定义ROI区域
center_indices = [4, 5]  # 中心区域的索引

# 初始化摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # 转换为灰度图像
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY)

    error = None
    any_region_triggered = False  # 是否有区域被触发

    for idx, r in enumerate(roi):
        x, y, w, h = r
        roi_img = binary[y:y+h, x:x+w]

        # 计算白色像素的比例
        white_percentage = np.mean(roi_img)

        # 如果白色像素的比例大于阈值，则认为该区域被触发
        if white_percentage > 127:
            any_region_triggered = True
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.drawMarker(frame, (center_x, center_y), (0, 255, 0), markerType=cv2.MARKER_CROSS, thickness=2)

            # 计算误差值
            if idx < center_indices[0]:  # 左侧区域
                current_error = idx - center_indices[0]
            elif idx > center_indices[1]:  # 右侧区域
                current_error = idx - center_indices[1]
            else:  # 中心区域
                current_error = 0

            # 更新误差值
            if error is None or abs(current_error) > abs(error):
                error = current_error

    # 如果没有任何区域被触发，则将误差值设为-4
    if not any_region_triggered:
        error = -4

    print("Error: %d" % error)

    # 显示图像
    cv2.imshow('frame', frame)

    # 按下 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头并关闭所有窗口
cap.release()
cv2.destroyAllWindows()
