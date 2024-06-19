from machine import Pin, SPI
import utime

# Requires ssd1306.py (from micropython-lib) saved on the Pico.
from ssd1306 import SSD1306_SPI # OLED driver
import framebuf # frame buffer used by the OLED driver

Count = 0 # counts the number of times button is pressed
Last_press = 0 # last time we pressed the button 

#--------------------
button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
#--------------------


# OLED resolution
SCREEN_WIDTH = 128 # columns
SCREEN_HEIGHT = 64 # rows


# Initialize I/O pins associated with the oled display SPI interface

spi_sck = Pin(18) # SPI0 SCK
spi_sda = Pin(19) # SPI0 TX (MOSI)
spi_res = Pin(21) # OLED reset
spi_dc  = Pin(20) # OLED data/command select
spi_cs  = Pin(17) # OLED chip select

#
# SPI bus number must match the wiring
#
SPI_DEVICE = 0 # OLED is wired to SPI0

#
# initialize the SPI interface for the OLED display
#
oled_spi = SPI( SPI_DEVICE, baudrate= 100000, sck= spi_sck, mosi= spi_sda )

#
# Initialize the display
#
oled = SSD1306_SPI( SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True )

def Button_Pressed(button):
    global Count, Last_press
    new_time = utime.ticks_ms()
    if(new_time-Last_press) > 50:
        Count += 1
        Last_press = new_time
    


button.irq(trigger=machine.Pin.IRQ_FALLING, handler=Button_Pressed)



# setup a timer when the switch is first closed or opened
# ignoring the bouncing signal for 1/5 of a second (200 msec)
# by then the button state has settled and the new value can be returned


while ( True ):

  
#
# Clear the buffer
#
        oled.fill(0)
        
#
# Update the text on the screen
#
        oled.text("FM Radio Menu", 15, 0) # Print the text starting from 0th column and 0th row
        oled.text("1 - change freq", 0, 10) # Menu entry at x=0, y=10
        oled.text("2 - change vol", 0, 20)
        oled.text("3 - mute audio", 0, 30)
        oled.text("4 - current sett", 0, 40)
        oled.text("Count is: %4d" % Count, 0, 50 ) # Print the value stored in the variable Count. 
        
#
# Draw box below the text
#
                

#
# Transfer the buffer to the screen
#
        oled.show()
