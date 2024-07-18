# -*- coding: utf-8 -*-
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

# print(Number_recognition)

from maix import camera, display, image
import serial

ser = serial.Serial("/dev/ttyS1", 115200)  # 连接串口
number_recognition = Number_recognition()
send_num = None
while True:
    img = camera.capture()
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
        ser.write(send_num.encode('utf-8'))
        send_num = None
    display.show(img)