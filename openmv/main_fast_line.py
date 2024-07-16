import time
from pyb import Pin, SPI
fbuf = bytearray(320)
cs  = Pin("P3", Pin.OUT_OD)
rst = Pin("P9", Pin.OUT_PP)
rs  = Pin("P8", Pin.OUT_PP)
servo1 = Pin("P6", Pin.OUT_PP)
servo2 = Pin("P7", Pin.OUT_PP)
USE_HORIZONTAL  = False
IMAGE_INVER	 = True
X_MIN_PIXEL = 0
Y_MIN_PIXEL = 0
if USE_HORIZONTAL:
	X_MAX_PIXEL = 128
	Y_MAX_PIXEL = 128
else:
	X_MAX_PIXEL = 128
	Y_MAX_PIXEL = 128
RED	 = 0XF800
GREEN   = 0X07E0
BLUE	= 0X001F
BLACK   = 0X0000
YELLOW  = 0XFFE0
WHITE   = 0XFFFF
CYAN	= 0X07FF
BRIGHT_RED = 0XF810
GRAY1   = 0X8410
GRAY2   = 0X4208
spi = SPI(2, SPI.MASTER, baudrate=int(10000000000/10), polarity=0, phase=0,bits=8)
def write_command_byte(c):
	cs.low()
	rs.low()
	spi.send(c)
	cs.high()
def write_data_byte(c):
	cs.low()
	rs.high()
	spi.send(c)
	cs.high()
def write_command(c, *data):
	write_command_byte(c)
	if data:
		for d in data:
			if d > 255:
				write_data_byte(d >> 8)
				write_data_byte(d&0xFF)
			else:
				write_data_byte(d)
def write_image(img):
	cs.low()
	rs.high()
	spi.send(img)
	cs.high()
def SetXY(xpos, ypos):
	write_command(0x2A, xpos>>8, xpos&0XFF)
	write_command(0x2B, ypos>>8, ypos&0XFF)
	write_command(0x2C)
def SetRegion(xStar, yStar, xEnd, yEnd):
	write_command(0x2A, xStar>>8, xStar&0XFF, xEnd>>8, xEnd&0XFF)
	write_command(0x2B, yStar>>8, yStar&0XFF, yEnd>>8, yEnd&0XFF)
	write_command(0x2C)
def DrawPoint(x, y, Color):
	SetXY(x, y)
	write_data_byte(Color >> 8)
	write_data_byte(Color&0XFF)
def ReadPoint(x, y):
	data = 0
	SetXY(x, y)
	write_data_byte(data)
	return data
def Clear(Color):
	global X_MAX_PIXEL, Y_MAX_PIXEL
	SetRegion(0, 0, X_MAX_PIXEL-1 , Y_MAX_PIXEL-1 )
	for i in range(0, Y_MAX_PIXEL):
		for m in range(0, X_MAX_PIXEL):
			write_data_byte(Color >> 8)
			write_data_byte(Color&0xFF)
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
	write_command(0xC0, 0x21)
	write_command(0xC1, 0x11)
	write_command(0xC5, 0x24, 0x3C)
	write_command(0xC7, 0xB7)
	if USE_HORIZONTAL:
		if IMAGE_INVER:
			write_command(0x36, 0xE8)
		else:
			write_command(0x36, 0x28)
	else:
		if IMAGE_INVER:
			write_command(0x36, 0xC8)
		else:
			write_command(0x36, 0x48)
	global X_MAX_PIXEL, Y_MAX_PIXEL
	SetRegion(0, 0, X_MAX_PIXEL - 1, Y_MAX_PIXEL - 1)
	write_command(0x3A, 0x55)
	write_command(0xB1, 0x00, 0x18)
	write_command(0xB7, 0x06)
	write_command(0x11)
	time.sleep_ms(120)
	write_command(0x29)
	write_command(0x2C)
def display(img):
	write_command(0x2C)
	write_image(img)
import sensor, image
from machine import UART
import time
from pyb import Pin, Timer, LED
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
LCDinit()
Clear(BLUE)
ch_21 = tim_2.channel(1, Timer.PWM, pin=Pin("P6"), pulse_width_percent=45)
ch_41 = tim_4.channel(1, Timer.PWM, pin=Pin("P7"), pulse_width_percent=45)
data = bytearray([0x5C,0x00,0x00,0x00,0x00,0xA5])
X_OFFSET = 0
Y_OFFSET = 0
ZOOM_AMOUNT = 1.5
x_rotation_counter = 0
y_rotation_counter = 0
z_rotation_counter = 270
FOV_WINDOW = 1
roi = [(i * 16, 100, 16, 40) for i in range(20)]
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
	is_right_angle = False
	is_left_angle = False
	consecutive_triggered_right = 0
	consecutive_triggered_left = 0
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
			elif idx > center_indices[1]:
				current_error = idx - center_indices[1]
			else:
				current_error = 0
			if error is None or abs(current_error) > abs(error):
				error = current_error
			
			# 检测右侧是否有连续10个ROI区域被触发
			if idx >= len(roi) // 2:
				consecutive_triggered_right += 1
				if consecutive_triggered_right >= 5:
					is_right_angle = True
			else:
				consecutive_triggered_right = 0
			
			# 检测左侧是否有连续10个ROI区域被触发
			if idx < len(roi) // 2:
				consecutive_triggered_left += 1
				if consecutive_triggered_left >= 5:
					is_left_angle = True
			else:
				consecutive_triggered_left = 0
		else:
			consecutive_triggered_right = 0
			consecutive_triggered_left = 0

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

	# 如果遇到右侧直角，直接设置data[1]和data[2]为0xff
	if is_right_angle:
		data[1] = 0xff
		data[2] = 0xff
	# 如果遇到左侧直角，直接设置data[1]和data[2]为0xee
	elif is_left_angle:
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
		uart.write(data)
		time.sleep_ms(200)
		data[1] = 0x00
		data[2] = 0x00
	if data[1] == 0xee and data[2] == 0xee :
		uart.write(data)
		time.sleep_ms(100)
		data[1] = 0x00
		data[2] = 0x00
	else :
		uart.write(data)
