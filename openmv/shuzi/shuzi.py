#   0------------>+x
#   |
#   |
#   |
#   |
#   |
#   v
#   +y

import sensor, image, time
from machine import UART

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QQVGA)
sensor.set_contrast(3)                              #设置对比度，范围-3~3
sensor.set_vflip(True)                              #垂直翻转图像
sensor.set_hmirror(True)                            #水平翻转图像
sensor.skip_frames(time = 2000)

clock = time.clock()

uart = UART(3, 9600)                                #使用串口3，波特率9600

mcu_packet_length = 10                              #接收方mcu的接收数据包长度
num_quantity = 8                                    #数字模板个数
num_model = []                                      #储存数字模型图片的列表，这里的数字图片模型高度40pix
threshold = (0, 60)                                 #寻找的数字色块灰度阈值
scale = 1                                           #缩放比例变量
num_lst = []                                        #用于存储识别到的数字

img_to_matching = sensor.alloc_extra_fb(35, 45, sensor.GRAYSCALE)   #声明一个35x45的画布，用于模板匹配

#将所有模板图片添加到列表（由于模板图片文件名为1、2、3...故可以这么用）
for n in range(1, num_quantity+1):
    num_model.append(image.Image('/shuzi/'+str(n)+'.pgm'))              #括号内为模板所在路径

while(True):
    clock.tick()
    img = sensor.snapshot()
    num_lst.append(0xFF)                                            #设置包头

    blobs = img.find_blobs([threshold])                             #按阈值寻找数字色块，结果可能为多组数据
    if blobs:                                                       #判断是否找到了色块
        for blob in blobs:                                          #依次循环每个色块
            if blob.pixels()>50 and 100>blob.h()>10 and blob.w()>3: #色块尺寸过滤
                scale = 40/blob.h()                                 #通过色块尺寸，计算需要的缩放比例
                #按坐标和比例提取色块（即摄像头拍到的数字），注意坐标长宽各扩大4个像素，避免图像不完整
                img_to_matching.draw_image(img, 0, 0, roi=(blob.x()-2, blob.y()-2, blob.w()+4,blob.h()+4), x_scale=scale, y_scale=scale)
                for n in range(0, num_quantity):                    #用所有数字模板和他匹配
                    #threshold 是浮点数（0.0~1.0），其中较小的值在提高检测速率同时增加误报率。
                    #step是查找模板时需要跳过的像素数量，用于提高速度。
                    r = img_to_matching.find_template(num_model[n], 0.7, step=2, search=image.SEARCH_EX)
                    if r:                                           #判断是否找到了数字
                        #给找到的数字画矩形框（“blob[0:4]”与“blob[0],blob[1],blob[2],blob[3]”等价）
                        img.draw_rectangle(blob[0:4], color=(255, 0, 0))
                        #注明数字几
                        img.draw_string(blob[0], blob[1], str(n+1), scale=2, color=(255, 0, 0))
                        num_lst.append((n+1))                       #将数字添加到列表末尾

    while(len(num_lst) < mcu_packet_length + 1):                    #如果发送数据包长度小于接收数据包长度
        num_lst.append(0x00)                                        #补满数据

    num_lst.append(0xFE)                                            #设置包尾
    print(num_lst)
    data = bytearray(num_lst)
    uart.write(data)                                                #将打包好的数据发送出去
    num_lst.clear()                                                 #清除列表，为下次做准备
