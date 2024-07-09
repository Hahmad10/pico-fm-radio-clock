from machine import Pin, SPI, RTC
from ssd1306 import SSD1306_SPI
import utime

# Screen dimensions
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

# SPI pins initialization
spi_sck = Pin(18)
spi_sda = Pin(19)
spi_res = Pin(21)
spi_dc = Pin(20)
spi_cs = Pin(17)

# Setup SPI device
# Comment on baudrate: Basically anything under 1MHz takes 28ms and anything over
#                      this takes 12ms to display the screen.
SPI_DEVICE = 0
oled_spi = SPI(SPI_DEVICE, baudrate=1100000, sck=spi_sck, mosi=spi_sda)
oled = SSD1306_SPI(SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True)

# RTC initialization
rtc = RTC()
rtc.datetime((2024, 7, 9, 2, 22, 0, 0, 0))

# Variables to control format and manage updates
time_format_24hr = True
last_displayed_time = None

def update_time():
    year, month, day, weekday, hour, minute, second, subsecond = rtc.datetime()
    if time_format_24hr:
        formatted_time = "{:02}:{:02}:{:02}".format(hour, minute, second)
    else:
        am_pm = "AM"
        if hour == 0:
            hour = 12
        elif hour >= 12:
            am_pm = "PM"
            if hour > 12:
                hour -= 12
        formatted_time = "{:02}:{:02} {}".format(hour, minute, am_pm)
    return formatted_time

def toggle_time_format():
    global time_format_24hr
    time_format_24hr = not time_format_24hr

# Define button and setup interrupt
button5 = Pin(5, Pin.IN, Pin.PULL_DOWN)
Last_press5 = 0

def Button_Pressed5(button):
    global Last_press5
    new_time5 = utime.ticks_ms()
    if(new_time5 - Last_press5) > 200:
        toggle_time_format()
        Last_press5 = new_time5

button5.irq(trigger=Pin.IRQ_FALLING, handler=Button_Pressed5)

while True:
    current_time = update_time()
    if current_time != last_displayed_time:
        # Calculate text width and height to update only changed area
        text_width = 8 * len(current_time)
        x = (SCREEN_WIDTH - text_width) // 2
        y = (SCREEN_HEIGHT - 8) // 2
        
        # Clear the specific area of the old time (optional if overwriting)
        oled.fill_rect(x, y, text_width, 8, 0)
        
        # Update time display
        oled.text(current_time, x, y)
        oled.show()
        
        last_displayed_time = current_time
    
    utime.sleep(1)

