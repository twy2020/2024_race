# 导入函数库
import sensor, image, time, math
from machine import UART
from pyb import UART

# 开启时钟
clock = time.clock() # 跟踪FPS帧率

# 变量初始化
# 阈值设置 根据实际情况进行更改
TRA_TH= [(128, 255)] # 巡线的灰度值 阈值[(0, 64)][(128, 255)]
TRA_AngTH=30 # 巡线时角度阈值

uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1)

# ROI区域设置
# (x,y,w,h,weight)=(矩形左上顶点的坐标(x,y),矩形宽度和高度(w,h),权重)
TRA_ROIS = [ # [ROI, weight]
    (0, 100, 160, 20, 0.7), # You'll need to tweak the weights for your app
    (0,  50, 160, 20, 0.3), # depending on how your robot is setup.
    (0,   0, 160, 20, 0.1)
]
Weight_Sum = 0 # 权值和初始化
for r in TRA_ROIS: Weight_Sum += r[4] # 计算权值和

# 通信数据包封装
Run = bytearray([0x24,0x4F,0x4D,0x56,0x31,0x26,0x23]) # $OMV1&#  直行
Left = bytearray([0x24,0x4F,0x4D,0x56,0x32,0x26,0x23]) # $OMV2&#  左转
Right = bytearray([0x24,0x4F,0x4D,0x56,0x33,0x26,0x23]) # $OMV3&#  右转
Stop = bytearray([0x24,0x4F,0x4D,0x56,0x34,0x26,0x23]) # $OMV4&#  停止

# Fun1:获得最大色块的位置索引函数
# 输入:N个色块(blobs) 输出:N个色块中最大色块的索引(int i)
def Get_MaxIndex(blobs):
    maxb_index = 0 # 最大色块索引初始化
    max_pixels = 0 # 最大像素值初始化
    for i in range(len(blobs)): # 对N个色块进行N次遍历
        if blobs[i].pixels() > max_pixels: # 当某个色块像素大于最大值
            max_pixels = blobs[i].pixels() # 更新最大像素
            maxb_index = i # 更新最大索引
            return maxb_index

# 摄像头初始化
sensor.reset() # 初始化相机传感器
sensor.set_pixformat(sensor.RGB565) # 设置相机模块的像素模式 16 bits/像素 GRAY为8
sensor.set_framesize(sensor.QQVGA) # 设置相机模块的帧大小 160x120
sensor.skip_frames(30) # 跳过30帧 让相机图像在改变相机设置后稳定下来
sensor.set_auto_gain(False) # 关闭自动增益
sensor.set_auto_whitebal(False) # 关闭默认的白平衡

# 主函数
OVSys_State = 1

while (1):
    clock.tick()
    if (OVSys_State == 1) or (OVSys_State == 3): # 循迹模式或者循迹避障模式
        sensor.set_pixformat(sensor.GRAYSCALE) # 循迹模式 设置摄像头为灰度图
        TRA_img = sensor.snapshot().histeq() # 截一帧图像 加强对比度好分割
        TRA_img.mean(1)
        TRA_img.binary([(0,35)])

        # 偏移角度计算
        Centroid_Sum = 0 # 初始化质心和
        for r in TRA_ROIS: # 是ROI的元组
            # 找到视野中ROI区域的色块,merge=true,将找到的图像区域合并
            blobs = TRA_img.find_blobs(TRA_TH, roi=r[0:4], pixels_threshold=100, area_threshold=100, merge=True)
            if blobs: # 如果找到了多个色块 计算质心和
                maxb_index = Get_MaxIndex(blobs) # 找到多个色块中的最大色块返回索引值
                # 返回最大色块外框元组(x,y,w,h) 绘制线宽为2的矩形框 不填充矩形
                TRA_img.draw_rectangle(blobs[maxb_index].rect(), thickness = 2, fill = False)
                # 最大色块的中心位置标记十字
                TRA_img.draw_cross(blobs[maxb_index].cx(), blobs[maxb_index].cy())
                # 计算质心和=(ROI中最大颜色块的中心点横坐标)cx*(ROI权值)w
                Centroid_Sum += blobs[maxb_index].cx() * r[4]

        # 中间公式 确定线心位置=质心和/权值和
        Center_Pos = (Centroid_Sum / Weight_Sum)
        Deflection_Angle = 0 # 需要将线心Center_Pos转换为偏角 偏角初始化为0
        Deflection_Angle = -math.atan((Center_Pos - 80) / 60) # 计算偏角 限制输出为正负53.13°
        Deflection_Angle = math.degrees(Deflection_Angle) # 弧度值转换为角度

        # 输出偏角数据
        print("Deflection Angle: %f" % Deflection_Angle)
