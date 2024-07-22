#导入相关模块
from maix import display, camera
import time

from maix import gpio #导入相关模块
#KEY 是 PH13,输入模式
KEY = gpio.gpio(13, "H", 1, 2)
#LED 是 PH14,默认输出模式
LED = gpio.gpio(14, "H", 1)

i = 0
while True:
    #实时显示摄像头拍摄图像
    img = camera.capture()

     #KEY 被按下
    if KEY.get_value() == 0:
        time.sleep(0.05) #延时消抖
        if KEY.get_value() == 0:
            i = i + 1
            LED.set_value(0) #点亮蓝灯
            img.save('/mnt/UDISK/photo/'+str(i)+'.jpg') #保存图片到photo文件夹
            while KEY.get_value() == 0: #等待按键释放
                pass
    else:
        LED.set_value(1) #熄灭蓝灯

    img.draw_string(0, 0, str(i), 1, (255, 0, 0), 1) #左上角信息拍照的张数
    display.show(img)
