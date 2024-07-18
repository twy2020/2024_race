# -*- coding: utf-8 -*-
import cv2
import numpy as np
THRESHOLD = 100  # Grayscale threshold for dark things.
roi = [(0, 100, 32, 40), (32, 100, 32, 40), (64, 100, 32, 40), (96, 100, 32, 40),
       (128, 100, 32, 40), (160, 100, 32, 40), (192, 100, 32, 40), (224, 100, 32, 40),
       (256, 100, 32, 40), (288, 100, 32, 40)]
center_indices = [4, 5]  

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY)

    error = None
    any_region_triggered = False 

    for idx, r in enumerate(roi):
        x, y, w, h = r
        roi_img = binary[y:y+h, x:x+w]

        white_percentage = np.mean(roi_img)

        if white_percentage > 127:
            any_region_triggered = True
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.drawMarker(frame, (center_x, center_y), (0, 255, 0), markerType=cv2.MARKER_CROSS, thickness=2)

            if idx < center_indices[0]: 
                current_error = idx - center_indices[0]
            elif idx > center_indices[1]: 
                current_error = idx - center_indices[1]
            else: 
                current_error = 0


            if error is None or abs(current_error) > abs(error):
                error = current_error

    if not any_region_triggered:
        error = -4

    print("Error: %d" % error)

    display.show(img) 