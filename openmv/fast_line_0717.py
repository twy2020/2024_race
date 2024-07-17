import sensor, image
from machine import UART
import time
from pyb import Pin, Timer, LED
bee  = Pin("P8", Pin.OUT_PP)
bee.high()
uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1)
tim_2 = Timer(2, freq=300)
tim_4 = Timer(4, freq=300)
THRESHOLD = (0, 100)
BINARY_VISIBLE = True
min_degree = 30
max_degree = 150
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
data = bytearray([0x5C,0x00,0x00,0x00,0x00,0xA5])
X_OFFSET = 0
Y_OFFSET = 0
ZOOM_AMOUNT = 1.4
x_rotation_counter = 0
y_rotation_counter = 0
z_rotation_counter = 270
FOV_WINDOW = 1
roi = [(i * 16,40, 16, 60) for i in range(20)]
center_indices = [9, 10]
LED(2).on()
time.sleep_ms(100)
LED(2).off()
LED(1).on()
time.sleep_ms(100)
LED(1).off()
LED(3).on()
time.sleep_ms(100)
LED(3).off()
LED(2).on()
bee.low()
time.sleep_ms(200)
bee.high()
while True:
    img = sensor.snapshot()\
                            .lens_corr(1.9)\
                            .rotation_corr(x_rotation = x_rotation_counter, \
                                            y_rotation = y_rotation_counter, \
                                            z_rotation = z_rotation_counter, \
                                            x_translation = X_OFFSET, \
                                            y_translation = Y_OFFSET, \
                                            zoom = ZOOM_AMOUNT, \
                                            fov = FOV_WINDOW)\
                                                                        .binary([THRESHOLD]) if BINARY_VISIBLE else sensor.snapshot()
    data[1] = 0x00
    data[2] = 0x00
    left_triggered_count = 0
    right_triggered_count = 0
    error = None
    any_region_triggered = False
    for idx, r in enumerate(roi):
        img.draw_rectangle(r, (255, 0, 0), 2)
        stats = img.get_statistics(roi=r)
        white_percentage = stats.mean()
        if white_percentage > 90:
            any_region_triggered = True
            center_x = r[0] + r[2] // 2
            center_y = r[1] + r[3] // 2
            img.draw_cross(center_x, center_y, (0, 255, 0), size=5)
            if idx < center_indices[0]:
                current_error = idx - center_indices[0]
                left_triggered_count += 1
            elif idx > center_indices[1]:
                current_error = idx - center_indices[1]
                right_triggered_count += 1
            else:
                current_error = 0
            if error is None or abs(current_error) > abs(error):
                error = current_error
        else:
            if idx < len(roi) // 2:
                left_triggered_count = 0
            else:
                right_triggered_count = 0
    if not any_region_triggered:
        LED(1).on()
        time.sleep_ms(10)
        LED(1).off()
    if error is not None:
        if error < 0:
            data[3] = 0x00
            data[4] = int(-error)
        elif error > 0:
            data[3] = 0x01
            data[4] = int(error)
        else:
            data[3] = 0x00
            data[4] = 0x00
    else:
        data[3] = 0x00
        data[4] = 0x00
    if right_triggered_count > left_triggered_count and right_triggered_count >= 5:
        data[1] = 0xff
        data[2] = 0xff
    elif left_triggered_count > right_triggered_count and left_triggered_count >= 5:
        data[1] = 0xee
        data[2] = 0xee
    else:
        line = img.get_regression([(255, 255) if BINARY_VISIBLE else THRESHOLD])
        if line:
            img.draw_line(line.line(), color=127)
            if line.theta() > 90:
                error1 = 180 - line.theta()
                if error1 > 5 and error1 < 30:
                    data[1] = 0x00
                    data[2] = int(error1)
                elif error1 > 30:
                    data[1] = 0x00
                    error1 = 30
                    data[2] = int(error1)
            elif line.theta() < 90:
                error1 = line.theta()
                if error1 > 5 and error1 < 30:
                    data[1] = 0x01
                    data[2] = int(error1)
                elif error1 > 30:
                    data[1] = 0x01
                    error1 = 30
                    data[2] = int(error1)
            else:
                data[1] = 0x00
                data[2] = 0x00
            LED(2).on()
            time.sleep_ms(10)
            LED(2).off()
            img.draw_line(160, 0, 160, 240, (255, 0, 0), 2)
    if data[1] == 0xff and data[2] == 0xff :
        data[3] = 0x00
        data[4] = 0x00
        uart.write(data)
        time.sleep_ms(50)
        bee.low()
        time.sleep_ms(50)
        bee.high()
        data[1] = 0x00
        data[2] = 0x00
    if data[1] == 0xee and data[2] == 0xee :
        data[3] = 0x00
        data[4] = 0x00
        uart.write(data)
        bee.low()
        time.sleep_ms(50)
        bee.high()
        time.sleep_ms(50)
        bee.low()
        time.sleep_ms(50)
        bee.high()
        data[1] = 0x00
        data[2] = 0x00
    else :
        uart.write(data)
