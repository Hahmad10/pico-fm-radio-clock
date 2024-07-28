from machine import Pin, SPI, I2C, Timer
from ssd1306 import SSD1306_SPI
from PicoClock_API import Clock # Import the clock class
from PicoTemp_API import Temperature  # Import the temperature class
from PicoRadio_API import Radio  # Import the radio class
import utime

# Setup radio
fm_radio = Radio(101.9, 4, True)  # Start muted

# Setup encoder pins
DT_Pin = Pin(6, Pin.IN, Pin.PULL_UP)
CLK_Pin = Pin(7, Pin.IN, Pin.PULL_UP)
SW = Pin(8, Pin.IN, Pin.PULL_UP)

previousValue = 1
last_button_press_time = 0

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
oled_spi = SPI(SPI_DEVICE, baudrate=100000, sck=spi_sck, mosi=spi_sda)
oled = SSD1306_SPI(SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True)

# Clock instance
clock = Clock()
temp_sensor = Temperature()

# Button setup
button1 = Pin(0, Pin.IN, Pin.PULL_DOWN)  # Time and Alarm Set
button2 = Pin(1, Pin.IN, Pin.PULL_DOWN)  # Time/Alarm Edit
button3 = Pin(2, Pin.IN, Pin.PULL_DOWN)  # 12/24 hr toggle
button4 = Pin(3, Pin.IN, Pin.PULL_DOWN)  # Snooze

last_press3 = 0

def button_pressed3(pin):
    global last_press3
    new_time3 = utime.ticks_ms()
    if (new_time3 - last_press3) > 50:
        clock.toggle_time_format()
        last_press3 = new_time3
        update_display(None)  # Update display immediately after toggling time format
        return True
    return False

# Set up interrupt for the button
button3.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed3)

def handle_encoder():
    global previousValue, hour, minute, setting_minutes, clock
    
    current_value = CLK_Pin.value()
    if current_value != previousValue:
        if CLK_Pin.value() == 0:
            if DT_Pin.value() == 0:
                if setting_minutes:
                    minute = (minute - 1) % 60
                else:
                    hour = (hour - 1) % (24 if clock.time_format_24hr else 12)
                    if not clock.time_format_24hr and hour == 0:
                        hour = 12
            else:
                if setting_minutes:
                    minute = (minute + 1) % 60
                else:
                    hour = (hour + 1) % (24 if clock.time_format_24hr else 12)
                    if not clock.time_format_24hr and hour == 0:
                        hour = 12
            previousValue = 1
            update_display(None)  # Update display immediately after changing value
            utime.sleep_ms(100)

def handle_button(pin, delay):
    global last_button_press_time, setting_minutes, clock_set
    current_time = utime.ticks_ms()
    if current_time - last_button_press_time > delay:  # Debounce the button
        last_button_press_time = current_time
        if not clock_set:
            if setting_minutes:
                clock.set_time(hour, minute)
                clock_set = True
            setting_minutes = not setting_minutes
            update_display(None)  # Update display immediately after handling button
        else:
            # Toggle mute
            new_mute_state = not fm_radio.Mute
            if fm_radio.SetMute(int(new_mute_state)):
                fm_radio.ProgramRadio()

def cleanup():
    fm_radio.SetMute(True)
    fm_radio.ProgramRadio()
    print("Radio muted for cleanup")
    
# Function to be called by the timer
def update_display(t):
    oled.fill(0)  # Clear the display

    if not clock_set:
        display_time = f"{hour:02}:{minute:02}"
        # Flash the digits while setting the time
        if int(utime.time() * (2/3)) % 2:
            if setting_minutes:
                display_time = f"{hour:02}:  "
            else:
                display_time = f"  :{minute:02}"
        oled.text("Set Time:", 0, 0)
        text_width = 8 * len(display_time)  # Calculate coordinates to center the text
        x = (SCREEN_WIDTH - text_width) // 2
        y = (SCREEN_HEIGHT - 8) // 2
        oled.text(display_time, x, y)
    else:
        current_time = clock.get_time()
        
        # Display time
        text_width = 8 * len(current_time)  # Calculate coordinates to center the text
        x = (SCREEN_WIDTH - text_width) // 2
        y = (SCREEN_HEIGHT - 8) // 2
        oled.text(current_time, x, y)
        
        # Display temperature in the top right corner, enclosed in a rectangle
        temp_text = f"{current_temp}C"
        temp_width = 8 * len(temp_text) + 4  # Plus some padding
        oled.rect(128 - temp_width - 1, 0, temp_width, 10, 1)  # Draw rectangle
        oled.text(temp_text, 128 - temp_width + 2, 1)  # Adjust text position for padding
    
    oled.show()

# Global variables for setting time
hour = 0
minute = 0
setting_minutes = False
clock_set = False

# Global variable to store the temperature
current_temp = temp_sensor.read_temp()

def update_temperature(t):
    global current_temp
    current_temp = temp_sensor.read_temp()

# Initialize the timer
display_timer = Timer()
temp_timer = Timer()
display_timer.init(period=500, mode=Timer.PERIODIC, callback=update_display)  # Update every 500ms
temp_timer.init(period=30000, mode=Timer.PERIODIC, callback=update_temperature)  # Update every 30sec

# Set up interrupt for the buttons
button1.irq(trigger=Pin.IRQ_FALLING, handler=handle_button)
button2.irq(trigger=Pin.IRQ_FALLING, handler=handle_button)

try:
    while True:
        handle_encoder()
        if SW.value() == 0:
            handle_button(SW,800)
            utime.sleep(0.1)  # Reduce frequency of main loop
except KeyboardInterrupt:
    cleanup()
    print("Program interrupted and cleaned up")
