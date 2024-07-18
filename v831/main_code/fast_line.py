from maix import camera, display, image
import cv2
import numpy as np

# 变量初始化
THRESHOLD = 100  # 灰度阈值
roi = [(0, 120, 24, 24), (24, 120, 24, 24), (48, 120, 24, 24), (72, 120, 24, 24),
       (96, 120, 24, 24), (120, 120, 24, 24), (144, 120, 24, 24), (168, 120, 24, 24),
       (192, 120, 24, 24), (216, 120, 24, 24)]
center_indices = [4, 5]  # 中间两个区域

def rotate_image(img, angle):
    if angle == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        return img

while True:
    img = camera.capture()  # 从摄像头中获取一张图像

    # 将图像数据转换为numpy数组
    img_data = np.frombuffer(img.tobytes(), dtype=np.uint8).reshape((img.height, img.width, 3))

    # 旋转图像（根据需要调整旋转角度）
    img_data = rotate_image(img_data, 90)
    
    # 将RGB图像转换为灰度图像
    img_gray = cv2.cvtColor(img_data, cv2.COLOR_RGB2GRAY)
    
    # 将灰度图像进行二值化处理
    _, img_binary = cv2.threshold(img_gray, THRESHOLD, 255, cv2.THRESH_BINARY)
    
    # 反转二值化图像
    img_binary_inv = cv2.bitwise_not(img_binary)
    
    # 计算误差
    error = None
    any_region_triggered = False  # 标记是否有任何区域被触发

    for idx, r in enumerate(roi):
        x, y, w, h = r
        roi_img = img_binary_inv[y:y+h, x:x+w]

        # 计算该区域的白色像素比例
        white_percentage = np.mean(roi_img)

        # 如果白色像素比例超过50%，绘制一个点并计算误差值
        if white_percentage > 127:
            any_region_triggered = True
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.drawMarker(img_data, (center_x, center_y), (0, 255, 0), markerType=cv2.MARKER_CROSS, thickness=2)

            # 计算误差值
            if idx < center_indices[0]:  # 左边区域
                current_error = idx - center_indices[0]
            elif idx > center_indices[1]:  # 右边区域
                current_error = idx - center_indices[1]
            else:  # 中间两个区域
                current_error = 0

            # 更新误差值
            if error is None or abs(current_error) > abs(error):
                error = current_error

    # 如果没有任何区域被触发，设置误差值为-4
    if not any_region_triggered:
        error = -4

    print("Error: %d" % error)

    # 将反转后的二值化灰度图像扩展为RGB格式
    img_binary_inv_rgb = cv2.cvtColor(img_binary_inv, cv2.COLOR_GRAY2RGB)

    # 将RGB图像转换回Maix Image格式以便显示
    img_binary_inv_rgb_maix = image.load(img_binary_inv_rgb.tobytes(), (img.width, img.height))

    display.show(img_binary_inv_rgb_maix)  # 将图像显示出来
