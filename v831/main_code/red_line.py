from maix import image, display, camera
import time

red = (10, 100, 30, 127, -37, 127) #红色
data = bytearray([0x5C,0x00,0x00,0xA5])
while True:
    
    img = camera.capture().rotate(180, adjust=0)
    line = img.find_line()
    img.draw_line(line["rect"][0], line["rect"][1], line["rect"][2],
                  line["rect"][3], color=(255, 255, 255), thickness=1)
    img.draw_line(line["rect"][2], line["rect"][3], line["rect"][4],
                  line["rect"][5], color=(255, 255, 255), thickness=1)
    img.draw_line(line["rect"][4], line["rect"][5], line["rect"][6],
                  line["rect"][7], color=(255, 255, 255), thickness=1)
    img.draw_line(line["rect"][6], line["rect"][7], line["rect"][0],
                  line["rect"][1], color=(255, 255, 255), thickness=1)
    img.draw_circle(line["cx"], line["cy"], 4,
                    color=(255, 255, 255), thickness=1)
    if line:
            if line.rotation * 180 / 3.14 > 90:
                error1 = 180 - line.rotation * 180 / 3.14 
                if error1 > 5 and error1 < 30:
                    data[1] = 0x00
                    data[2] = int(error1)
                elif error1 > 30:
                    data[1] = 0x00
                    error1 = 30
                    data[2] = int(error1)
            elif line.rotation * 180 / 3.14  < 90:
                error1 = line.rotation * 180 / 3.14 
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
    display.show(img.rotate(180, adjust=0))