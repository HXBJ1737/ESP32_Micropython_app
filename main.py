import st7789
from uQR import QRCode
from machine import SPI, Pin, I2C, SoftI2C, ADC, Timer, RTC, PWM, UART
from dht20 import DHT20
import time
from ubinascii import *
import ntptime
import gc
import random
import micropython
import vga1_16x32 as font
import vga1_8x16 as font1
from chinese import Chine
import _thread
import sys
import network
import dht
import esp
import socket
import urequests

esp.osdebug(None)

# 垃圾回收

gc.enable()
gc.collect()

# ------------------------------------------------------
# tft

tft = st7789.ST7789(SPI(1,
                        baudrate=80_000_000,
                        polarity=0,
                        sck=Pin(12),
                        mosi=Pin(11)),
                    240,
                    240,
                    reset=Pin(18, Pin.OUT),
                    cs=Pin(10, Pin.OUT),
                    dc=Pin(9, Pin.OUT),
                    backlight=Pin(13, Pin.OUT),
                    rotation=1,
                    options=0,
                    buffer_size=0)

tft.init()
# ------------------------------------------------------
# 土壤湿度

soil_up, soil_down = 1100, 1000
soil_m = ADC(Pin(1))
soil_m.atten(ADC.ATTN_11DB)
# ------------------------------------------------------
# 紫光灯
PUR_led = Pin(2, Pin.OUT)
PUR_led.value(1)


def PUR_LED_ON():
    PUR_led.value(0)


def PUR_LED_OFF():
    PUR_led.value(1)


# ------------------------------------------------------

# LED

led = Pin(15, Pin.OUT)
led.value(1)


def LED_ON():
    led.value(0)


def LED_OFF():
    led.value(1)

# ------------------------------------------------------

#换气风扇
fan=Pin(16,Pin.OUT)
fan.value(0)
def FAN_ON():
    fan.value(1)

def FAN_OFF():
    fan.value(0)
# ------------------------------------------------------

#加湿器
enhum=Pin(21,Pin.OUT)
enhum.value(0)

def ENHUM_ON():
    enhum.value(1)

def ENHUM_OFF():
    enhum.value(0)
# ------------------------------------------------------
# ------------------------------------------------------

# 无源蜂鸣器

ulfreq = 10000
buzzer = PWM(Pin(17))
buzzer.freq(ulfreq)


def Buzzer(flag: bool):
    uld = 100 if flag is True else 0
    buzzer.duty(uld)


Buzzer(False)

# ------------------------------------------------------

# 舵机

servo = PWM(Pin(47, Pin.OUT))
servo.freq(50)


def Servoangle(x):
    servo.duty_u16((int)((3277 / 90) * x + 1638))


Servoangle(0)
# ------------------------------------------------------

# CO2
CO2=0
uart = UART(2, baudrate=9600, rx=46, tx=45, timeout=10)


def ByteToHex(bins):
    return ''.join(["%02X" % x for x in bins]).strip()


def CO2_data():
    global CO2
    if (uart.any()):
        data1 = uart.read(6)
        data = ByteToHex(data1)[2:6]
        datah = int(data[0:2], 16)
        datal = int(data[2:4], 16)
        CO2 = 256 * datah + datal
        print(CO2)
    # time.sleep(0.1)


def CO2_FAN_AUTO():
    global CO2
    CO2_data()
    if CO2>600:
        FAN_ON()
    elif CO2<550:
        FAN_OFF()
# ------------------------------------------------------
# DHT20

i2c = I2C(0, scl=Pin(3), sda=Pin(8), freq=400_000)
dht20 = DHT20(i2c)


def dht_data():
    temper = dht20.temperature()
    humidity = dht20.humidity()
    print("temper :    " + str(temper))
    print("humidity : " + str(humidity))


def read_sensor():
    global temp, temp_percentage, hum, hum_percentage
    temp = temp_percentage = hum = hum_percentage = 0
    try:
        dht20.measure()
        temp = dht20.temperature()
        hum = dht20.humidity()
        # print(f"tem:{temp},hum:{hum}")

        if (isinstance(temp, float)
                and isinstance(hum, float)) or (isinstance(temp, int)
                                                and isinstance(hum, int)):
            msg = '{0:3.1f},{1:3.1f}'.format(temp, hum)
            temp_percentage = (temp + 6) / (50 + 6) * (100)
            hum_percentage = (hum - 20) / (90 - 20) * 100
            #             print(f"temp_percentage:{temp_percentage}")
            #             print(f"hum_percentage:{hum_percentage}")
            #             print(f"msg:{msg}")
            hum = round(hum, 2)
            return (msg)
        else:
            return ('Invalid sensor readings.')
    except OSError:
        return ('Failed to read sensor.')


# ------------------------------------------------------

# 光照度

# i2c1 = SoftI2C(scl=Pin(39), sda=Pin(40), freq=10000)  #软件I2C
i2c1 = I2C(1, scl=Pin(39), sda=Pin(40), freq=400_000)
addr_list = i2c1.scan()
# print('addr_list:',addr_list)
# result = bh1750fvi.sample(i2c) # in lux
# print(result)
# BH1750通电，进入等待测量状态
i2c1.writeto(addr_list[0], b'\x01')
# 设置分辨率模式为连续 H分辨率模式
i2c1.writeto(addr_list[0], b'\x10')


def GY_30_sensor():
    global result, result_percentage
    data = i2c1.readfrom(35, 2)
    result = round(float(data[0] * 0xff + data[1]) / 1.2, 1)
    result1 = (int)((data[0] * 0xff + data[1]) / 1.2)
    result_percentage = ((result) / 2000) * (100)
    return result1, result_percentage


# ------------------------------------------------------
# 按键开关

key1 = Pin(4, Pin.IN, Pin.PULL_UP)
key2 = Pin(5, Pin.IN, Pin.PULL_UP)
key3 = Pin(6, Pin.IN, Pin.PULL_UP)
key4 = Pin(7, Pin.IN, Pin.PULL_UP)


def key():
    key_Get = 0
    if key1.value() == 0:
        time.sleep_ms(7)
        while key1.value() == 0:
            continue
        time.sleep_ms(7)
        key_Get = 1
    if key2.value() == 0:
        time.sleep_ms(7)
        while key2.value() == 0:
            continue
        time.sleep_ms(7)
        key_Get = 2
    if key3.value() == 0:
        time.sleep_ms(7)
        while key3.value() == 0:
            continue
        time.sleep_ms(7)
        key_Get = 3
    if key4.value() == 0:
        time.sleep_ms(7)
        while key4.value() == 0:
            continue
        time.sleep_ms(7)
        key_Get = 4

    return key_Get


# ------------------------------------------------------

# 定时器

# timer = Timer(-1)
# timer.init(period=1500, mode=Timer.PERIODIC, callback=dht11())
# ------------------------------------------------------

# wifi

ip = str()
ssid = 'iQOO_Neo5'
password = 'death001'


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print('connecting to network...')
    wlan.connect(ssid, password)
    i = 1
    while wlan.isconnected() == False:
        print("正在链接...{}".format(i))
        tft.text(font, "connecting.{}".format(i), 30, 108, st7789.WHITE)
        i += 1
        time.sleep(1)
    tft.text(font, "connecting", 40, 30, st7789.color565(0, 255, 255))
    tft.text(font, "successful", 40, 65, st7789.color565(5, 20, 255))
    time.sleep(1)
    print('network config:', wlan.ifconfig())
    return wlan.ifconfig()[0]


# ------------------------------------------------------
# 二维码


def show_qrcode(ip):
    tft.fill(st7789.color565(255, 255, 255))  # 背景设置为白色
    qr = QRCode(border=2)
    qr.add_data(
        'http://{}'.format(ip))  # ip  192.168.31.157--->http://192.168.31.157
    matrix = qr.get_matrix()

    row_len = len(matrix)
    col_len = len(matrix[0])

    print("row=%d, col=%d" % (row_len, col_len))

    # 放大倍数
    scale_rate = 8

    # 准备黑色，白色数据
    buffer_black = bytearray(scale_rate * scale_rate * 2)  # 每个点pixel有2个字节表示颜色
    buffer_white = bytearray(scale_rate * scale_rate * 2)  # 每个点pixel有2个字节表示颜色
    color_black = st7789.color565(0, 0, 0)
    color_black_byte1 = color_black & 0xff00 >> 8
    color_black_byte2 = color_black & 0xff
    color_white = st7789.color565(255, 255, 255)
    color_white_byte1 = color_white & 0xff00 >> 8
    color_white_byte2 = color_white & 0xff

    for i in range(0, scale_rate * scale_rate * 2, 2):
        buffer_black[i] = color_black_byte1
        buffer_black[i + 1] = color_black_byte2
        buffer_white[i] = color_white_byte1
        buffer_white[i + 1] = color_white_byte2

    # 循环次数不增加，只增加每次发送的数据量，每次发送scale_rate X scale_rate个点的信息
    for row in range(row_len):
        for col in range(col_len):
            if matrix[row][col]:
                #tft.pixel(row, col, st7789.color565(0, 0, 0))
                tft.blit_buffer(buffer_black, row * scale_rate,
                                col * scale_rate, scale_rate, scale_rate)
            else:
                #tft.pixel(row, col, st7789.color565(255, 255, 255))
                tft.blit_buffer(buffer_white, row * scale_rate,
                                col * scale_rate, scale_rate, scale_rate)
            col += 1
        row += 1


# ------------------------------------------------------
# 网页


def web_page():
    if led.value() == 1:
        led_state = 'checked'
    else:
        led_state = ""
    html = """<html>

<head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta http-equiv="refresh" content="1.4">
    <style>
        body {
            width: 100%%;
            text-align: center;
            flex-direction: column;
        }
        .progress {
            background-color: transparent;
            position: absolute;
            top: 30px;
        }

        .progress.vertical {
            position: relative;
            left: -3%%;
            width: 7%%;
            height: 60%%;
            display: inline-block;
            margin: 20px;
        }

        .progress.vertical>.progress-bar {
            width: 100%% !important;
            position: absolute;
            bottom: 0;
            transform: translate(-50%%, 0);
        }

        .progress-bar {
            background: linear-gradient(to top, #f5af19 0%%, #f12711 100%%);
            position: absolute;

        }

        .progress-bar-light_intensity {
            background: linear-gradient(to top, #0e0e0e 0%%, #ffffff 100%%);
            position: absolute;
        }

        .progress-bar-hum {
            background: linear-gradient(to top, #9CECFB 0%%, #65C7F7 50%%, #0052D4 100%%);

        }

        p {
            position: absolute;
            font-size: 20px;
            color: #f12711;
            top: 100%%;
            left: 0%%;
            transform: translate(-50%%, -50%%);
            z-index: 5;
        }

        .switch {
            position: absolute;
            display: inline-block;
            width: 120px;
            height: 50px;
            bottom: 5%%;
            left: 50%%;
            transform: translate(-50%%, -50%%);
        }

        .switch input {
            display: none;
        }

        .slider {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            border-radius: 34px;
        }

        span {
            position: absolute;
            padding-top: 15;
            color: #0052D4;
        }

        .silder:before {
            position: absolute;
            content: "";
            height: 52px;
            width: 52px;
            left: 8px;
            bottom: 8px;
            background-color: #fff;
            -webkit-transition: .4s;
            transition: .4s;
            border-radius: 68px;
        }

        input:checked+.slider {
            background-color: #2196F3
        }

        input:checked+.slider:before {
            -webkit-transform: translateX(52px);
            -ms-transform: translateX(52px);
            transform: translateX(52px);
        }
    </style>
</head>

<body>
    <h1>ESP Web Server</h1>
    <ul>
        <div class="progress vertical">
            <p style="color: #0e0e0e;">Lux:</p>
            <p style="color: #0e0e0e; top: 105%%;">%(result)s</p>
            <div role="progressbar" style="height: %(result_percentage)s%%;" class="progress-bar progress-bar-light_intensity"></div>
        </div>
        <div class="progress vertical">
            <p style="color: #d03f06;">Tem:</p>
            <p style="color: #d03f06; top: 105%%;">%(temp)s</p>
            <div role="progressbar" style="height:%(temp_percentage)s%%;" class="progress-bar"></div>
        </div>
        <div class="progress vertical">
            <p style="color: #0c8abb;">Hum:</p>
            <p style="color: #0c8abb; top: 105%%;">%(hum)s</p>
            <div role="progressbar" style="height:%(hum_percentage)s%%;" class="progress-bar progress-bar-hum"></div>
        </div>
    </ul>
    <label class="switch">

        <input type="checkbox" onchange="toggleCheckbox(this)" %(led_state)s>
        <span class="slider">led&nbspcontrol</span>
    </label>
    <script>
        function toggleCheckbox(element) {
            var xhr = new XMLHttpRequest();
            if (element.checked) { xhr.open("GET", "/?led=on", true); }
            else { xhr.open("GET", "/?led=off", true); }
            xhr.send();
        }
    </script>
</body>

</html>""" % {
        "result": result,
        "result_percentage": result_percentage,
        "temp": temp,
        "temp_percentage": temp_percentage,
        "hum": hum,
        "hum_percentage": hum_percentage,
        "led_state": led_state
    }
    return html


# ------------------------------------------------------

# 时间


def sync_ntp():
    ntptime.NTP_DELTA = 3155644800
    while True:
        try:
            ntptime.host = 'ntp1.aliyun.com'
            ntptime.settime()
            return
        except OSError as e:
            print(e)
            continue


rtc = None
# ------------------------------------------------------
# 中文


class ShowChinese:

    def ByteOpera16x32(self, num, dat):
        byte = [0x01, 0x02, 0x04, 0x8, 0x10, 0x20, 0x40, 0x80]
        if dat & byte[num]:
            return 1
        else:
            return 0  #n字符，x宽度，y高度，r,g,b 565编码颜色

    def LcdShowCh_16x32(self, n, x_axis, y_axis, r, g, b):
        for i in range(4):
            for a in range(32):
                for b in range(8):
                    if (self.ByteOpera16x32(b, Chine.chine[n * 128 + i * 32 +
                                                           a])):
                        tft.pixel(x_axis + a, y_axis + i * 8 + b,
                                  st7789.color565(r, g, b))  #改变括号里数值可以改变字体颜色
                    else:
                        tft.pixel(x_axis + a, y_axis + i * 8 + b,
                                  st7789.color565(0, 0, 0))

    def showCN(self, index, x, y, r, g, b):
        self.LcdShowCh_16x32(index, x, y, r, g, b)


cn = ShowChinese()

# ------------------------------------------------------


class Button:

    def __init__(self, ):
        pass

    def TextBox(
        self,
        x: int,
        y: int,
        content: str,
    ):
        pass


# 天气

Url = 'https://api.seniverse.com/v3/weather/now.json?key=Skx0Fj-ecQWIs6MW9&location=zhengzhou&language=zh-Hans&unit=c'
r = None
# ------------------------------------------------------


class UI(Button):

    decoded_index = list()
    decoded_wifi_0 = list()
    decoded_wifi_1 = list()
    decoded_home = list()
    decoded_menu = list()
    decoded_uqr = list()
    decoded_config = list()
    decoded_data = list()
    decoded_ul = list()
    decoded_control=list()
    decoded_zhengzhou=list()
    decoded_qing=list()
    decoded_duoyun=list()
    decoded_yin=list()
    decoded_xiaoyu=list()
    decoded_zhongyu=list()
    decoded_dayu=list()
    decoded_sheshidu=list()



    def __init__(self, ):
        pass

    def Reload(self):
        start = time.ticks_ms()
        tft.text(font, "decoding...", 20, 150, st7789.color565(0, 0, 255))
        self.decoded_mainpageimg = tft.jpg_decode('img/index_240x77.jpg')
        self.decoded_wifi_0 = tft.jpg_decode('img/wifi_0_45x45.jpg')
        self.decoded_wifi_1 = tft.jpg_decode('img/wifi_1_45x45.jpg')
        self.decoded_home = tft.jpg_decode('img/Home_icon_45x45.jpg')
        self.decoded_menu = tft.jpg_decode('img/menu_45x45.jpg')
        self.decoded_uqr = tft.jpg_decode('img/uqr.jpg')
        self.decoded_config = tft.jpg_decode('img/config_240x240.jpg')
        self.decoded_data = tft.jpg_decode('img/data_240x240.jpg')
        self.decoded_ul = tft.jpg_decode('img/ul_240x240.jpg')

        self.decoded_control = tft.jpg_decode('img/control_240x240.jpg')
        self.decoded_zhengzhou = tft.jpg_decode('img/zhengzhou_50x26.jpg')
        self.decoded_qing = tft.jpg_decode('img/qing_50x50.jpg')
        self.decoded_duoyun = tft.jpg_decode('img/duoyun_50x50.jpg')
        self.decoded_yin = tft.jpg_decode('img/yin_50x50.jpg')
        self.decoded_xiaoyu = tft.jpg_decode('img/xiaoyu_50x50.jpg')
        self.decoded_zhongyu = tft.jpg_decode('img/zhongyu_50x50.jpg')
        self.decoded_dayu = tft.jpg_decode('img/dayu_50x50.jpg')
        self.decoded_sheshidu = tft.jpg_decode('img/sheshidu_50x45.jpg')
        print(f"decode:{(time.ticks_ms() -start)/1000}s")
        tft.text(font, f"decode:{(time.ticks_ms() - start)/1000}s", 10, 150,
                 st7789.color565(0, 0, 255))
        print(micropython.mem_info())
        global ip, r, rtc
        ip = do_connect()
        sync_ntp()
        rtc = RTC()
        print("ip地址是：", ip)
        tft.text(font, ip, 0, 150, st7789.color565(0, 0, 255))
        r = urequests.get(Url)
        r.json()

    def Date_time(self, year, month, day, dayofweek, hour, minu, sec):
        month = str(month) if month > 9 else '0' + str(month)
        day=day if hour<16 else day+1
        day = str(day) if day > 9 else '0' + str(day)
        hour = hour - 16 if hour < 24 and hour > 15 else hour + 8
        hour = str(hour) if hour > 9 else '0' + str(hour)
        minu = str(minu) if minu > 9 else '0' + str(minu)
        sec = str(sec) if sec > 9 else '0' + str(sec)

        tft.text(font,
                 str(year) + '-' + str(month) + '-' + str(day), 40, 126,
                 st7789.color565(0, 0, 255))
        tft.text(font,
                 str(hour) + ':' + str(minu) + ':' + str(sec), 55, 158,
                 st7789.color565(0, 0, 255))

    def Wifi_icon(self, flag: bool):
        if flag == False:
            tft.blit_buffer(self.decoded_wifi_0[0], 0, 0,
                            self.decoded_wifi_0[1], self.decoded_wifi_0[2])
        else:
            tft.blit_buffer(self.decoded_wifi_1[0], 0, 0,
                            self.decoded_wifi_1[1], self.decoded_wifi_1[2])

    def Menu_icon(self):
        tft.blit_buffer(self.decoded_menu[0], 0, 195, self.decoded_menu[1],
                        self.decoded_menu[2])

    def Home_icon(self, ):
        tft.blit_buffer(self.decoded_home[0], 97, 195, self.decoded_home[1],
                        self.decoded_home[2])

    def Uqr_icon(self, ):
        tft.blit_buffer(self.decoded_uqr[0], 195, 195, self.decoded_uqr[1],
                        self.decoded_uqr[2])

    def Wall_paper(self, ):
        tft.blit_buffer(self.decoded_mainpageimg[0], 0, 57,
                        self.decoded_mainpageimg[1],
                        self.decoded_mainpageimg[2])

    def Data(self, ):
        tft.blit_buffer(self.decoded_data[0], 0, 0, self.decoded_data[1],
                        self.decoded_data[2])
        while True:
            if status == 0:
                return
            msg1 = read_sensor()
            msg2 = GY_30_sensor()[0]

            soiladi = 4095 - soil_m.read()
            CO2_FAN_AUTO()
            angle = msg2 * 9 / 1000 if msg2 < 10000 else 90
            Servoangle(angle)
            if soiladi < 10:
                soilad = " " + str(soiladi) + "  "
            elif soiladi < 100:
                soilad = " " + str(soiladi) + " "
            elif soiladi < 1000:
                soilad = str(soiladi)
            else:
                soilad = str(soiladi)

            if msg2 < 10:
                msg2 = " " + str(msg2) + "   "
            elif msg2 < 100:
                msg2 = " " + str(msg2) + "  "
            elif msg2 < 1000:
                msg2 =" " + str(msg2) + " "
            elif msg2 < 10000:
                msg2 =" "+ str(msg2)
            else:
                msg2 = str(msg2)

            CO2_FAN_AUTO()
            if (int)(msg1[5] + msg1[6])<79:
                ENHUM_ON()
            else:
                ENHUM_OFF()
            tft.text(font, msg2, 120, 16,
                     st7789.color565(59, 107, 255))
            tft.text(font, msg1[0] + msg1[1], 130, 60,
                     st7789.color565(59, 107, 255))
            tft.text(font, msg1[5] + msg1[6], 130, 105,
                     st7789.color565(59, 107, 255))
            tft.text(font, str(CO2), 120, 150, st7789.color565(59, 107, 255))
            tft.text(font, soilad, 120, 195, st7789.color565(59, 107, 255))

    def Weather(self, ):
        print(r.json()['results'][0]['location']['name'],
              r.json()['results'][0]['now']['temperature'],
              r.json()['results'][0]['now']['text'])
        #         cn.showCN(40, 48, 10, 255, 108, 0)
        #         cn.showCN(41, 81, 10, 255, 108, 0)
        tft.blit_buffer(self.decoded_zhengzhou[0], 52, 10, self.decoded_zhengzhou[1],
                        self.decoded_zhengzhou[2])
        tft.text(font,
                 r.json()['results'][0]['now']['temperature'], 114, 12,
                 st7789.color565(255, 108, 0))
        #         cn.showCN(8, 146, 10, 255, 108, 100)
        tft.blit_buffer(self.decoded_sheshidu[0], 144, 5, self.decoded_sheshidu[1],
                        self.decoded_sheshidu[2])

        if r.json()['results'][0]['now']['text'] == '晴':
            tft.blit_buffer(self.decoded_qing[0], 190, 0, self.decoded_qing[1],
                        self.decoded_qing[2])
            #cn.showCN(0, 196, 10, 255, 108, 100)
        elif r.json()['results'][0]['now']['text'] == '阴':
            tft.blit_buffer(self.decoded_yin[0], 190, 0, self.decoded_yin[1],
                        self.decoded_yin[2])
            #cn.showCN(3, 196, 10, 255, 108, 100)
        elif r.json()['results'][0]['now']['text'] == '小雨' or r.json(
        )['results'][0]['now']['text'] == '雨':
            tft.blit_buffer(self.decoded_xiaoyu[0], 190, 0, self.decoded_xiaoyu[1],
                        self.decoded_xiaoyu[2])
            #cn.showCN(4, 176, 10, 255, 108, 100)
            #cn.showCN(7, 208, 10, 255, 108, 100)
        elif r.json()['results'][0]['now']['text'] == '中雨':
            tft.blit_buffer(self.decoded_zhongyu[0], 190, 0, self.decoded_zhongyu[1],
                        self.decoded_zhongyu[2])
            #cn.showCN(4, 176, 10, 255, 108, 100)
            #cn.showCN(7, 208, 10, 255, 108, 100)
        elif r.json()['results'][0]['now']['text'] == '多云':
            tft.blit_buffer(self.decoded_duoyun[0], 190, 0, self.decoded_duoyun[1],
                        self.decoded_duoyun[2])
        # cn.showCN(1, 176, 10, 255, 108, 100)
        # cn.showCN(2, 208, 10, 255, 108, 100)
        elif r.json()['results'][0]['now']['text'] == '大雨':
            tft.blit_buffer(self.decoded_dayu[0], 190, 0, self.decoded_dayu[1],
                        self.decoded_dayu[2])
        # cn.showCN(6, 176, 10, 255, 108, 100)
        # cn.showCN(7, 208, 10, 255, 108, 100)

    def Main_Page(self, ):
        tft.fill(0)
        self.Wall_paper()
        self.Home_icon()
        self.Menu_icon()
        self.Uqr_icon()
        self.Wifi_icon(True)
        self.Weather()

    def Main_Page_open(self, ):
        self.Wall_paper()
        self.Home_icon()
        self.Menu_icon()
        self.Uqr_icon()
        self.Wifi_icon(False)
        time.sleep(1.5)
        self.Wifi_icon(True)
        self.Weather()

    def Menu_Page(self, ):
        pass


    def Control(self,):
        tft.blit_buffer(self.decoded_control[0], 0, 0, self.decoded_control[1],
                        self.decoded_control[2])
        fanflag=False
        ledflag=False
        layflag=False
        humflag=False
        while True:
            if status == 0:
                return
            if fanflag == False:
                FAN_OFF()
                tft.text(font, 'OFF', 180, 28, st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            else:
                FAN_ON()
                tft.text(font, "ON" + " ", 180, 28,
                         st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            if ledflag == False:
                LED_OFF()
                tft.text(font, 'OFF', 180, 85, st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            else:
                LED_ON()
                tft.text(font, "ON" + " ", 180, 85,
                         st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            if layflag == False:
                PUR_LED_OFF()
                tft.text(font, 'OFF', 180, 140, st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            else:
                PUR_LED_ON()
                tft.text(font, "ON" + " ", 180, 140,
                         st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            if humflag == False:
                ENHUM_OFF()
                tft.text(font, 'OFF', 180, 195, st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            else:
                ENHUM_ON()

            keyget = key()
            if keyget == 1:
                fanflag = True if fanflag == False else False
                humflag = True if humflag == False else False

            elif keyget == 2:
                ledflag = True if ledflag == False else False
            elif keyget == 3:
                layflag = True if layflag == False else False



    def Config_Page(self, ):
        tft.blit_buffer(self.decoded_config[0], 0, 0, self.decoded_config[1],
                        self.decoded_config[2])
        tft.text(font,
                 str(esp.flash_size() / 1024 / 1024) + "MB", 76, 28,
                 st7789.color565(59, 107, 255), st7789.color565(7, 7, 7))
        tft.text(font, '7.81MB', 76, 85, st7789.color565(59, 107, 255),
                 st7789.color565(7, 7, 7))
        tft.text(font, 'ESP32-S3', 76, 140, st7789.color565(59, 107, 255),
                 st7789.color565(7, 7, 7))
        tft.text(font, '2023.07.17', 70, 195, st7789.color565(59, 107, 255),
                 st7789.color565(7, 7, 7))
        while True:
            if status == 0:
                return

    def Ul_page(self, ):
        global ulfreq
        ulflag = False
        tft.blit_buffer(self.decoded_ul[0], 0, 0, self.decoded_ul[1],
                        self.decoded_ul[2])
        while True:
            if ulfreq < 10:
                ulfreqstr = "  " + str(ulfreq) + "Hz" + "  "
            elif ulfreq < 100:
                ulfreqstr = " " + str(ulfreq) + "Hz" + "  "
            elif ulfreq < 1000:
                ulfreqstr = " " + str(ulfreq) + "Hz" + " "
            elif ulfreq < 10000:
                ulfreqstr = " " + str(ulfreq) + "Hz"
            else:
                ulfreqstr = str(ulfreq) + "Hz"
            tft.text(font1, ulfreqstr, 170, 195, st7789.color565(59, 107, 255),
                     st7789.color565(0, 0, 0))
            if status == 0:
                return
            if ulflag == False:
                Buzzer(False)
                tft.text(font, 'OFF', 180, 28, st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            else:
                Buzzer(True)
                tft.text(font, "ON" + " ", 180, 28,
                         st7789.color565(59, 107, 255),
                         st7789.color565(0, 0, 0))
            keyget = key()
            if keyget == 1:
                ulflag = True if ulflag == False else False
            elif keyget == 2:
                ulfreq = ulfreq + 1000 if ulfreq >= 950 else ulfreq + 50
            elif keyget == 3:
                ulfreq = ulfreq - 1000 if ulfreq > 1000 else ulfreq - 50
            buzzer.freq(ulfreq)


# ------------------------------------------------------

status = 0
uqrflag = False
ui = UI()

# ------------------------------------------------------


def irqh(*argc):
    global status, uqrflag
    if status != 0:
        status = 0
        #ui.Main_Page()
        return


# ------------------------------------------------------
key4.irq(trigger=Pin.IRQ_LOWLEVEL, handler=irqh)
key4.irq(trigger=Pin.IRQ_FALLING, handler=irqh)
ui.Reload()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(128)

# 浏览器


def browser():
    global s
    while True:
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        gc.collect()
        request = conn.recv(1024)
        result, result_percentage = GY_30_sensor()
        sensor_readings = read_sensor()
        print(result, result_percentage, sensor_readings)
        request = str(request)
        print('Content = %s' % request)
        led_on = request.find('led=on')
        led_off = request.find('led=off')
        print(led_on)
        if led_on == 8:
            print('LED ON')
            led.value(1)
        if led_off == 8:
            print('LED OFF')
            led.value(0)
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
        if status == 0:
            return


def main():
    global status, uqrflag, rtc
    tft.fill(0)
    ui.Main_Page_open()
    while True:
        msg, no = GY_30_sensor()
        #         angle=180 if msg>1000 else 0
        angle = msg * 9 / 1000 if msg < 10000 else 90
        Servoangle(angle)
        if status == 0:
            ui.Date_time(rtc.datetime()[0],
                         rtc.datetime()[1],
                         rtc.datetime()[2],
                         rtc.datetime()[3],
                         rtc.datetime()[4],
                         rtc.datetime()[5],
                         rtc.datetime()[6])
        keyget = key()
        if keyget == 1:
            status = 1
            ui.Data()
            ui.Main_Page()
            ENHUM_OFF()
            FAN_OFF()
        elif keyget == 2:
            status = 2
            ui.Control()
            ui.Main_Page()
        elif keyget == 3:
            status = 3
            show_qrcode(ip)
            uqrflag = True
            browser()
            ui.Main_Page()
        elif keyget == 4:
            status = 4
            ui.Ul_page()
            ui.Main_Page()


# def main():
#     do_connect()
#     while True:
#         dht_data()
#         CO2_data()
#         time.sleep(0.5)

if __name__ == "__main__":
    main()
