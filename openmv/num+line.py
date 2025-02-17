import time
import image
from pyb import Pin, SPI
fbuf = bytearray(160)  # 建立帧缓冲区，对于每个RGB565像素，帧缓冲区都需2字节

# IO接线：
# SDO/MISO  ---> P1(MISO)        如果不读LCD颜色，可不接
# LED       ---> P6 (背光控制)     可直接 接VCC，开机亮屏
# SCK       ---> P2(SCLK)          SCLK 时钟线
# SDI/MOSI  ---> P0(MOSI)          SDA 数据线
# DO/RS     ---> P8                数据命令选择线
# RESET     ---> P7                复位线
# CS        ---> P3                片选线
# GND       ---> GND
# VCC       ---> 3.3V

cs  = Pin("P3", Pin.OUT_OD)
rst = Pin("P8", Pin.OUT_PP)
rs  = Pin("P7", Pin.OUT_PP)
bl  = Pin("P6", Pin.OUT_PP)     # 背光控制

# 定义横屏/竖屏
USE_HORIZONTAL  = True         # 定义横屏
IMAGE_INVER     = True         # 旋转180°

# TFT resolution 240*320
X_MIN_PIXEL = 0
Y_MIN_PIXEL = 0
if USE_HORIZONTAL:
    X_MAX_PIXEL = 160               # 定义屏幕宽度
    Y_MAX_PIXEL = 128               # 定义屏幕高度
else:
    X_MAX_PIXEL = 160              # 定义屏幕宽度
    Y_MAX_PIXEL = 128               # 定义屏幕高度

# 常用颜色表                       #可去除
RED     = 0XF800
GREEN   = 0X07E0
BLUE    = 0X001F
BLACK   = 0X0000
YELLOW  = 0XFFE0
WHITE   = 0XFFFF

CYAN    = 0X07FF
BRIGHT_RED = 0XF810
GRAY1   = 0X8410
GRAY2   = 0X4208

# OpenMV  SPI2 总线  8位数据模式
spi = SPI(2, SPI.MASTER, baudrate=int(10000000000/66*0.06), polarity=0, phase=0, bits=8)

# SPI 写命令
def write_command_byte(c):
    cs.low()
    rs.low()
    spi.send(c)
    cs.high()

# SPI 写数据
def write_data_byte(c):
    cs.low()
    rs.high()
    spi.send(c)
    cs.high()

def write_command(c, *data): #命令数据一起写，先写命令 第二个开始为数据位。如果只写一个，则代表不写数据只写命令。
    write_command_byte(c)
    if data:
        for d in data:
            if d > 255:
                write_data_byte(d >> 8)
                write_data_byte(d & 0xFF)
            else:
                write_data_byte(d)

def write_image(img,mode=0):
    cs.low()
    rs.high()
    if mode ==1:
        spi.send(img)
    # 修改代码的核心
    else:
        if(True): #全发
            for m in img:                   #把一帧图像的对象取出来，放到帧缓存区中
                fbuf = m
                for i in range(0, 160):     #每行每行的发送
                    spi.send(fbuf[i] >> 8)  #先发第N行的第I个数据的高八位
                    spi.send(fbuf[i] & 0xFF) #再发低八位
        else: #只发一行固定的数据
            for i in range(0, 128):
                spi.send(fbuf[i])
                spi.send(fbuf[i+1] & 0xFF)
    cs.high()

def SetXY(xpos, ypos):
    write_command(0x2A, xpos >> 8, xpos & 0xFF)
    write_command(0x2B, ypos >> 8, ypos & 0xFF)
    write_command(0x2C)

def SetRegion(xStar, yStar, xEnd, yEnd):
    write_command(0x2A, xStar >> 8, xStar & 0xFF, xEnd >> 8, xEnd & 0xFF)
    write_command(0x2B, yStar >> 8, yStar & 0xFF, yEnd >> 8, yEnd & 0xFF)
    write_command(0x2C)

# 在指定位置绘制一个点
def DrawPoint(x, y, Color):
    SetXY(x, y)
    write_data_byte(Color >> 8)
    write_data_byte(Color & 0xFF)

def ReadPoint(x, y):
    data = 0
    SetXY(x, y)
    write_data_byte(data)
    return data

def Clear(Color):
    global X_MAX_PIXEL, Y_MAX_PIXEL
    SetRegion(0, 0, X_MAX_PIXEL - 1, Y_MAX_PIXEL - 1)
    for i in range(0, Y_MAX_PIXEL):
        for m in range(0, X_MAX_PIXEL):
            write_data_byte(Color >> 8)
            write_data_byte(Color & 0xFF)

def LCDinit():
    rst.low()
    time.sleep_ms(100)
    rst.high()
    time.sleep_ms(100)

    write_command(0xCB, 0x39, 0x2c, 0x00, 0x34, 0x02)
    write_command(0xCF, 0x00, 0XAA, 0XE0)
    write_command(0xE8, 0x85, 0x11, 0x78)
    write_command(0xEA, 0x00, 0x00)
    write_command(0xED, 0x67, 0x03, 0X12, 0X81)
    write_command(0xF7, 0x20)
    write_command(0xC0, 0x21)       # Power control, VRH[5:0]
    write_command(0xC1, 0x11)       # Power control, SAP[2:0];BT[3:0]
    write_command(0xC5, 0x24, 0x3C) # VCM control, 对比度调节
    write_command(0xC7, 0xB7)       # VCM control2, --
    # Memory Data Access Control
    if USE_HORIZONTAL:      # //C8   //48 68竖屏//28 E8 横屏
        if IMAGE_INVER:
            write_command(0x36, 0xE0)   # 从右到左 e8/68, 这里设置D3为0 (RGB)
        else:
            write_command(0x36, 0x20)   # 从左到右 28, 这里设置D3为0 (RGB)
    else:
        if IMAGE_INVER:
            write_command(0x36, 0xC0)   # 从下到上刷, 这里设置D3为0 (RGB)
        else:
            write_command(0x36, 0x40)   # 从上到下刷, 这里设置D3为0 (RGB)

    global X_MAX_PIXEL, Y_MAX_PIXEL
    SetRegion(0, 0, X_MAX_PIXEL - 1, Y_MAX_PIXEL - 1)

    # Interface Pixel Format
    write_command(0x3A, 0x55)

    write_command(0xB1, 0x00, 0x18)
    write_command(0xB6, 0x08, 0x82, 0x27)   # Display Function Control
#    write_command(0xF2, 0x00)               # 3Gamma Function Disable
#    write_command(0x26, 0x01)               # Gamma curve selected
    write_command(0xB7, 0x06)

    # set gamma
#    write_command(0xE0, 0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E, 0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)
#    write_command(0XE1, 0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31, 0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)

    write_command(0x11) # sleep_ms Exit
    time.sleep_ms(120)

    # Display On
    write_command(0x29)
    write_command(0x2C)
    bl.high()   # 拉背光

def display(img,mode):
    write_command(0x2C)
    write_image(img,mode)

import sensor, image
from machine import UART
import time
from pyb import Pin, Timer, LED
sensor.reset() # Initialize the camera sensor.
sensor.set_pixformat(sensor.RGB565) # or sensor.GRAYSCALE
sensor.set_framesize(sensor.QQVGA) # Special 128x160 framesize for LCD Shield.
sensor.skip_frames(time = 2000)
sensor.set_hmirror(False) # 水平镜像图像
sensor.set_vflip(False) # 垂直翻转图像
LCDinit() # Initialize the lcd screen.
Clear(BLUE)
X_OFFSET = 0
Y_OFFSET = 0
ZOOM_AMOUNT = 1.5
x_rotation_counter = 0
y_rotation_counter = 0
z_rotation_counter = 0
FOV_WINDOW = 1
BINARY_VISIBLE = True

blobs_threshold = (0, 60)
binary_threshold = (72, 156)
red_threshold = [(0, 57, 4, 83, -128, 127)]  # 红色的颜色阈值范围
THRESHOLD = (0, 100)  # Grayscale threshold for dark things.
#DrawPoint(50, 50, RED)
#display(sensor.snapshot())
uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1)

cmd = 0
ready = 1
data = bytearray([0x5C,0x00,0x00,0xA5])

num_quantity = 8  #数字模板个数
num_model = []

scale = 1
#将所有模板图片添加到列表（由于模板图片文件名为1、2、3...故可以这么用）
for n in range(1, num_quantity+1):
    num_model.append(image.Image('/shuzi/'+str(n)+'.pgm'))              #括号内为模板所在路径
send_num = bytearray([0x5B,0x00,0x00,0xA5])

GET_READY = bytearray([0x5D,0x01,0x01,0xA5])
uart.write(GET_READY)

while True:
    if uart.any():  # 检查是否有数据可读
        res = uart.read(3)  # 读取3个字节
        if res and len(res) == 3:  # 确保读取的数据长度为3
            if res[0] == 0x5A and res[2] == 0xA5:  # 检查帧头和帧尾
                cmd = res[1]  # 提取命令
                res = 0
                #print("Received command:", cmd)
#    if cmd == 0:
#        pass

#    elif cmd == 1:
#        ready == 1
#        uart.write(GET_READY)
#        cmd = 0

    if cmd == 2 and ready == 1:
        uart.write(GET_READY)
        sensor.set_hmirror(True) # 水平镜像图像
        sensor.set_vflip(True) # 垂直翻转图像
        sensor.set_pixformat(sensor.GRAYSCALE) # or sensor.GRAYSCALE
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
            uart.write(data)
            # 创建一个新的RGB565图像
            #print(line.theta())
    elif cmd ==3 and ready == 1:
        sensor.set_pixformat(sensor.RGB565)
        img_to_matching = sensor.alloc_extra_fb(35, 45, sensor.GRAYSCALE)   #声明一个35x45的画布，用于模板匹配
        sensor.set_vflip(True) # 垂直翻转图像
        sensor.set_hmirror(True) # 水平镜像图像
        img = sensor.snapshot()
        blobs = img.find_blobs([blobs_threshold])                             #按阈值寻找数字色块，结果可能为多组数据
        if blobs:                                                       #判断是否找到了色块
            for blob in blobs:                                          #依次循环每个色块
                if blob.pixels()>50 and 100>blob.h()>10 and blob.w()>3: #色块尺寸过滤
                    scale = 40/blob.h()                                 #通过色块尺寸，计算需要的缩放比例
                    #按坐标和比例提取色块（即摄像头拍到的数字），注意坐标长宽各扩大4个像素，避免图像不完整
                    img_to_matching.draw_image(img, 0, 0, roi=(blob.x()-2, blob.y()-2, blob.w()+4,blob.h()+4), x_scale=scale, y_scale=scale)
                    for n in range(0, num_quantity):                    #用所有数字模板和他c匹配
                        #threshold 是浮点数（0.0~1.0），其中较小的值在提高检测速率同时增加误报率。
                        #step是查找模板时需要跳过的像素数量，用于提高速度。
                        r = img_to_matching.find_template(num_model[n], 0.7, step=2, search=image.SEARCH_EX)
                        if r:                                           #判断是否找到了数字
                            #给找到的数字画矩形框（“blob[0:4]”与“blob[0],blob[1],blob[2],blob[3]”等价）
                            img.draw_rectangle(blob[0:4], color=(255, 0, 0))
                            #注明数字几
                            img.draw_string(blob[0], blob[1], str(n+1), scale=2, color=(255, 0, 0))
                            send_num[1] = int(n+1)
                            uart.write(send_num)
                            send_num[1] = 0
                            print(n+1)
        img.replace(hmirror=1)
        display(img,0)
        img.replace(hmirror=1)

    else:
        pass


