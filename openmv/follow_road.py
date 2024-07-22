#main.py -- put your code here!
import cpufreq
import pyb
import sensor,image, time,math
from pyb import LED,Timer,UART

sensor.reset()                      # 重置感光元件，重置摄像机
sensor.set_pixformat(sensor.RGB565) # 设置颜色格式为RGB565，彩色，每个像素16bit。
sensor.set_framesize(sensor.QQQVGA)  # 图像大小为QQQVGA，大小80x60
sensor.skip_frames(time = 2000)     #延时跳过一些帧，等待感光元件变稳定
sensor.set_auto_gain(False)          #黑线不易识别时，将此处写False
sensor.set_auto_whitebal(False)     #颜色识别必须关闭白平衡，会影响颜色识别效果，导致颜色的阈值发生改变
clock = time.clock()                # 创建一个时钟对象来跟踪FPS。
#sensor.set_auto_exposure(True, exposure_us=5000) # 设置自动曝光sensor.get_exposure_us()

red_led = pyb.LED(1)    #下面这三个就是OpenMV上的LED初始化
green_led = pyb.LED(2)
blue_led = pyb.LED(3)
uart=UART(3,115200)   #初始化串口3，波特率为115200，P4为TX连接单片机RX，P5为RX连接单片机TX

class target_check(object):
    x=0          #int16_t,横线上被标记黑点的地方，从左到右依次减少
    y=0          #int8_t,竖线上被标记黑点的地方，从上到下依次减少

target=target_check()


# 绘制水平线
def draw_hori_line(img, x0, x1, y, color):
    for x in range(x0, x1):
        img.set_pixel(x, y, color)
# 绘制竖直线
def draw_vec_line(img, x, y0, y1, color):
    for y in range(y0, y1):
        img.set_pixel(x, y, color)
# 绘制矩形
def draw_rect(img, x, y, w, h, color):
    draw_hori_line(img, x, x+w, y, color)
    draw_hori_line(img, x, x+w, y+h, color)
    draw_vec_line(img, x, y, y+h, color)
    draw_vec_line(img, x+w, y, y+h, color)


#图像大小为QQQVGA，大小80x60
#roi的格式是(x, y, w, h)
track_roi=[(0,25,5,10),
           (5,25,5,10),
           (10,25,5,10),
           (15,25,5,10),
           (20,25,5,10),
           (25,25,5,10),
           (30,25,5,10),
           (35,25,5,10),
           (40,25,5,10),
           (45,25,5,10),
           (50,25,5,10),
           (55,25,5,10),
           (60,25,5,10),
           (65,25,5,10),
           (70,25,5,10),
           (75,25,5,10)]

target_roi=[(70,0,10,12),
           (70,12,10,12),
           (70,24,10,12),
           (70,36,10,12),
           (70,48,10,12)]


thresholds =(0, 30, -30, 30, -30, 30)  #黑色的颜色阈值

hor_bits=['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0'] #记录横线16个感兴趣区是否为黑线
ver_bits=['0','0','0','0','0',]  #记录右边5个感兴趣区是否为黑线
#__________________________________________________________________
def findtrack():
    target.x=0
    target.y=0
    img=sensor.snapshot()

    #用于检测黑线
    for i in range(0,16):
        hor_bits[i]=0
        '''
        thresholds表示黑色线阈值，roi为感兴趣区
        merge=True，表示所有合并所有重叠的blob为一个
        margin 边界，如果设置为10，那么两个blobs如果间距10一个像素点，也会被合并。
        '''
        blobs=img.find_blobs([thresholds],roi=track_roi[i],merge=True,margin=10)
        #如果识别到了黑线，hor_bits对应位置1
        for b in blobs:
            hor_bits[i]=1

    #用于检测右侧的黑线
    for i in range(0,5):
        ver_bits[i]=0
        blobs=img.find_blobs([thresholds],roi=target_roi[i],merge=True,margin=10)
        for b in blobs:
            ver_bits[i]=1

    #绘制16个横线红色四个角
    for k in range(0,16):
        if  hor_bits[k]:
            target.x=target.x|(0x01<<(15-k))
            img.draw_circle(int(track_roi[k][0]+track_roi[k][2]*0.5),int(track_roi[k][1]+track_roi[k][3]*0.5),1,(255,0,0))
    #绘制右侧5个红色四个角
    for k in range(0,5):
        if  ver_bits[k]:
            target.y=target.y|(0x01<<(4-k))
            img.draw_circle(int(target_roi[k][0]+target_roi[k][2]*0.5),int(target_roi[k][1]+target_roi[k][3]*0.5),3,(0,255,0))
    #绘制16个横线感兴趣区
    for rec in track_roi:
        img.draw_rectangle(rec, color=(0,0,255))#绘制出roi区域
    #绘制右侧5个横线感兴趣区
    for rec in target_roi:
        img.draw_rectangle(rec, color=(0,255,255))#绘制出roi区域
           #大--小  从左到右                       从上到下
    print((target.x & 0xff00)>>8,target.x & 0xff,target.y)
    uart.write(str((target.x & 0xff00)>>8))
    #uart.write(str(target.x & 0xff))
    #uart.write(str(target.y))
    #uart.write("\r\n")

#__________________________________________________________________
def package_blobs_data():
    return bytearray([target.x >> 8,
                      target.x,
                      target.y])
#__________________________________________________________________
i = 0
while True:
    findtrack()
    uart.write(package_blobs_data())
    uart.write("\r\n")
    i = i + 1
    if i == 50:
        i = 0
        green_led.toggle()
    pyb.delay(10)
    #uart.write("Hello World!\r")
    #uart.write(1+'\n')
    #计算fps
    #print(clock.fps())
#__________________________________________________________________
