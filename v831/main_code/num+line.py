from maix import display, camera, image, nn, time, pinmap
import serial

#Devices_Init
# 初始化摄像头，调整分辨率
CAP_X = 320
CAP_Y = 200
cam = camera.Camera(CAP_X, CAP_Y)
disp = display.Display() 
# pinmap.set_pin_function("A19", "UART1_TX")
# pinmap.set_pin_function("A18", "UART1_RX")
device = "/dev/ttyS0"
ser = serial.Serial(device,115200,timeout=0.03)

#Data_Package_Init
send_num = bytearray([0x5B,0x00,0x00,0x00,0x00,0xA5])
data = bytearray([0x5C,0x00,0x00,0x00,0x00,0xA5])
GET_READY = bytearray([0x5D,0x01,0x01,0x00,0x00,0xA5])
cross_pp = bytearray([0x5E,0x01,0x00,0x00,0x00,0xA5])

num_label = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}

thresholds = [[0, 82, -5, 80, 10, 80]]
P_thresholds = [[7, 46, -46, 8, -32, 14]]  # Parking
blobs = []
valid_blobs = []
cmd = 3
detector = nn.YOLOv5(model="/root/models/model_120311.mud")
# ready_flag = 0

#Init_Done


while True:
    if ser.in_waiting > 0:
        res = ser.read(3)
        if res and len(res) == 3:  # 确保读取的数据长度为3
            if res[0] == 0x5A and res[2] == 0xA5:  # 检查帧头和帧尾
                cmd = res[1]  # 提取命令
                #ready_flag = 1
                res = 0
    # if ready_flag == 0:
    #     ser.write(GET_READY)
    #     time.sleep_ms(100)
    if cmd == 2: 
        cap = cam.read().lens_corr(strength=1.8, zoom=1.0)
        cap_copy = cap.copy()
        img = cap.binary(thresholds)
        #p_img = cap_copy.binary(P_thresholds)
        blobs = cap_copy.find_blobs([[100,100,0,0,0,0]], pixels_threshold=800)
        for blob in blobs:
            if abs(blob[2] - blob[3]) < 6 and (blob[2] * blob[3]) < 900:
                cross_pp[1] = 0x00
                cross_pp[2] = 0x00
                cross_pp[3] = 0x01
                cross_pp[4] = 0x00
                #print(1)
                ser.write(cross_pp)
            #img.draw_rect(blob[0], blob[1], blob[2], blob[3], image.COLOR_GREEN)

        lines = img.get_regression([[100,100,0,0,0,0]], area_threshold = 300) 
        for a in lines:
            theta = a.theta()
            rho = a.rho()
            if theta > 90:
                theta = 270 - theta
            else:
                theta = 90 - theta
            img.draw_string(0, 0, "theta: " + str(theta) + ", rho: " + str(rho), image.COLOR_BLUE)
            if theta > 65 and theta < 125:
                img.draw_line(a.x1(), a.y1(), a.x2(), a.y2(), image.COLOR_GREEN, 2)
                error1 = 90 - theta
                if error1 > 0:
                    if error1 > 1 and error1 < 15:
                        data[1] = 0x01
                        data[2] = int(error1)
                    elif error1 > 15:
                        data[1] = 0x01
                        error1 = 15
                        data[2] = int(error1)
                    #print(error1)
                    img.draw_string(0, 10, "STOP",image.COLOR_RED)
                elif error1 < 0:
                    if error1 > 1 and error1 < 15:
                        data[1] = 0x00
                        data[2] = int(abs(error1))
                    elif error1 > 15:
                        data[1] = 0x00
                        error1 = 15
                        data[2] = int(error1)
                    #print(error1)
                else:
                    data[1] = 0x00
                    data[2] = 0x00
                l_x = (a.x1() + a.x2()) / 2
                error2 = l_x - CAP_X / 2   
                #error2
                if error2 > 0:
                    data[3] = 0x01
                    data[4] = int(error2)
                    #print(error2)
                elif error2 < 0:
                    data[3] = 0x00
                    data[4] = int(abs(error2))
                    #print(error2)
                ser.write(data)
                img.draw_string(0, 0, "theta: " + str(theta) + ", rho: " + str(rho), image.COLOR_BLUE)
            elif theta >= 0 and theta <= 10 and (a.y1() + a.y2())/2 > CAP_Y / 2 or theta >= 170 and theta <= 180 and (a.y1() + a.y2())/2 > CAP_Y / 2:
                img.draw_line(a.x1(), a.y1(), a.x2(), a.y2(), image.COLOR_RED, 2)
                cross_pp[1] = 0x01
                cross_pp[2] = 0x00
                cross_pp[3] = 0x00
                cross_pp[4] = 0x00
                ser.write(cross_pp)
                #print("find clossing!")
            else:
                img.draw_line(a.x1(), a.y1(), a.x2(), a.y2(), image.COLOR_BLUE, 2)
        disp.show(img)
    if cmd == 3:
        #cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
        img = cam.read()
        objs = detector.detect(img, conf_th = 0.7, iou_th = 0.45)
        for obj in objs:
            if obj.class_id in num_label:
                img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
                label = num_label[obj.class_id]  # 使用字典来获取标签名称
                msg = f'{label}: {obj.score:.2f}'
                img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)

                num = obj.class_id  # 这里num是类ID，不是字符串
            if (2 * obj.x + obj.w) / 2 < CAP_X / 2:
                send_num[1] = int(num)    
                send_num[2] = 0x01 #Left
            elif (2 * obj.x + obj.w) / 2 > CAP_X / 2:
                send_num[1] = int(num)    
                send_num[2] = 0x02 #Right
            else:
                send_num[1] = 0x00    
                send_num[2] = 0x00
            ser.write(send_num)
            #print(send_num)
        disp.show(img)
