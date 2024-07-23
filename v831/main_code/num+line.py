from maix import image, display, camera
import time
import serial

red = (10, 100, 30, 127, -37, 127) #红色
data = bytearray([0x5C,0x00,0x00,0xA5])
GET_READY = bytearray([0x5D,0x01,0x01,0xA5])
ser = serial.Serial("/dev/ttyS1",115200,timeout=0.03)
ser.write(GET_READY)

cmd = 0
ready = 1

send_num = None
NUM_PACK = bytearray([0x5B,0x00,0x00,0xA5])

class Number_recognition:
    labels = ["1", "2", "3", "4", "5", "6", "7", "8"]
    anchors = [2.44, 2.25, 5.03, 4.91, 3.5 , 3.53, 4.16, 3.94, 2.97, 2.84]
    model = {
        "param": "/root/number_awnn.param",
        "bin": "/root/number_awnn.bin"
    }
    options = {
        "model_type":  "awnn",
        "inputs": {
            "input0": (224, 224, 3)
        },
        "outputs": {
            "output0": (7, 7, (1+4+len(labels))*5)
        },
        "mean": [127.5, 127.5, 127.5],
        "norm": [0.0078125, 0.0078125, 0.0078125],
    }
    w = options["inputs"]["input0"][1]
    h = options["inputs"]["input0"][0]

    def __init__(self):
        from maix import nn
        from maix.nn import decoder
        self.m = nn.load(self.model, opt=self.options)
        self.yolo2_decoder = decoder.Yolo2(len(self.labels), self.anchors, net_in_size=(self.w, self.h), net_out_size=(7, 7))

    def map_face(self, box):  # 将224*224空间的位置转换到240*240空间内
        def tran(x):
            return int(x / 224 * 240)

        box = list(map(tran, box))
        return box

number_recognition = Number_recognition()
    
while True:
    if ser.in_waiting > 0:
        res = ser.read(3)
        if res and len(res) == 3:  # 确保读取的数据长度为3
            if res[0] == 0x5A and res[2] == 0xA5:  # 检查帧头和帧尾
                cmd = res[1]  # 提取命令
                res = 0
    
    if cmd == 2 and ready == 1:    
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
        rotation = line['rotation']* 180 / 3.14 
        if line:
                if rotation > 90:
                    error1 = 180 - rotation
                    if error1 > 5 and error1 < 30:
                        data[1] = 0x00
                        data[2] = int(error1)
                    elif error1 > 30:
                        data[1] = 0x00
                        error1 = 30
                        data[2] = int(error1)
                elif rotation < 90:
                    error1 = rotation
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
        ser.write(data)
        display.show(img.rotate(180, adjust=0))
    elif cmd ==3 and ready == 1:
        img = camera.capture().rotate(180, adjust=0)
        AI_img = img.copy().resize(224, 224)
        out = number_recognition.m.forward(AI_img.tobytes(), quantize=True, layout="hwc")
        boxes, probs = number_recognition.yolo2_decoder.run(out, nms=0.3, threshold=0.5, img_size=(240, 240))

        for i, box in enumerate(boxes):
            class_id = probs[i][0]
            prob = probs[i][1][class_id]
            disp_str = "{}:{:.2f}%".format(number_recognition.labels[class_id], prob * 100)
            font_wh = image.get_string_size(disp_str)
            box = number_recognition.map_face(box)
            img.draw_rectangle(box[0], box[1], box[0] + box[2], box[1] + box[3], color=(255, 0, 0), thickness=2)
            img.draw_rectangle(box[0], box[1] - font_wh[1], box[0] + font_wh[0], box[1], color=(255, 0, 0))
            img.draw_string(box[0], box[1] - font_wh[1], disp_str, color=(255, 0, 0))
            send_num = number_recognition.labels[class_id]
        #print(send_num)
        if send_num is not None:
            NUM_PACK[1] = int(send_num.encode('utf-8'))
            ser.write(NUM_PACK)
            send_num = None
        display.show(img.rotate(180, adjust=0))