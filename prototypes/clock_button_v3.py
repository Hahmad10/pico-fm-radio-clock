from machine import Pin, SPI, RTC
from ssd1306 import SSD1306_SPI
import utime

# Define columns and rows of the OLED display
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

# Initialize I/O pins associated with the OLED display SPI interface
spi_sck = Pin(18)
spi_sda = Pin(19)
spi_res = Pin(21)
spi_dc = Pin(20)
spi_cs = Pin(17)

# SPI device setup
SPI_DEVICE = 0
oled_spi = SPI(SPI_DEVICE, baudrate=1100000, sck=spi_sck, mosi=spi_sda)
oled = SSD1306_SPI(SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True)

# Initialize RTC (Real-Time Clock)
rtc = RTC()
rtc.datetime((2024, 7, 9, 2, 12, 59, 50, 0))  # Set the RTC to 10 PM

time_format_24hr = True  # Global variable to control time format
colon_visible = True  # Initialize colon visibility flag

def update_time():
    year, month, day, weekday, hour, minute, second, subsecond = rtc.datetime()
    global colon_visible
    colon = ':' if colon_visible else ' '
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
        formatted_time = "{:02}{:}{:02} {}".format(hour, colon, minute, am_pm)
    return formatted_time

def toggle_time_format():
    global time_format_24hr
    time_format_24hr = not time_format_24hr

# Define the button and interrupt handler
button5 = Pin(5, Pin.IN, Pin.PULL_DOWN)
Last_press5 = 0

def Button_Pressed5(button):
    global Last_press5
    new_time5 = utime.ticks_ms()
    if(new_time5 - Last_press5) > 50:
        toggle_time_format()  # Toggle the time format
        Last_press5 = new_time5

# Set up interrupt for the button
button5.irq(trigger=Pin.IRQ_FALLING, handler=Button_Pressed5)

while True:
    oled.fill(0)
    current_time = update_time()
    text_width = 8 * len(current_time)  # Calculate coordinates to center the text
    x = (SCREEN_WIDTH - text_width) // 2
    y = (SCREEN_HEIGHT - 8) // 2
    oled.text(current_time, x, y)
    oled.show()
    colon_visible = not colon_visible  # Toggle colon visibility
    utime.sleep(0.5)  # Update every half second
