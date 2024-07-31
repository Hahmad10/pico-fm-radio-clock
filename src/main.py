from machine import Pin, SPI, I2C, Timer
from ssd1306 import SSD1306_SPI
from PicoClock_API import Clock  # Import the clock class
from PicoTemp_API import Temperature  # Import the temperature class
from PicoRadio_API import Radio  # Import the radio class
from PicoAlarm_API import Alarm  # Import the alarm class
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
alarm = Alarm(buzzer_pin=15, snooze_pin=3)

# Button setup
button1 = Pin(0, Pin.IN, Pin.PULL_DOWN)  # Time and Alarm Set
button2 = Pin(1, Pin.IN, Pin.PULL_DOWN)  # Time/Alarm Edit
button3 = Pin(2, Pin.IN, Pin.PULL_DOWN)  # 12/24 hr toggle
button4 = Pin(3, Pin.IN, Pin.PULL_DOWN)  # Snooze

last_press3 = 0
last_press2 = 0
last_press1 = 0
count_press2 = 0
detected_press2 = False
setting_channel = False
setting_integer_part = True

def button_pressed3(pin):
    global last_press3
    new_time3 = utime.ticks_ms()
    if (new_time3 - last_press3) > 50:
        print("toggling time format")
        clock.toggle_time_format()
        last_press3 = new_time3
        update_display(None)  # Update display immediately after toggling time format

def button_pressed2(pin):
    global detected_press2, count_press2, last_press2, clock_set, alarm_set
    new_time2 = utime.ticks_ms()
    if (new_time2 - last_press2) > 200:
        last_press2 = new_time2
        count_press2 += 1
        detected_press2 = True
        print(count_press2)

def button_pressed1(pin):
    global last_press1, setting_channel, setting_integer_part
    new_time1 = utime.ticks_ms()
    if (new_time1 - last_press1) > 50:
        print("Setting channel")
        setting_channel = True
        setting_integer_part = True  # Reset to start by setting the integer part
        last_press1 = new_time1
        update_display(None)  # Update display immediately after entering channel setting mode

def edit_time_or_alarm():
    global detected_press2, count_press2, clock_set, alarm_set, editing_time, editing_alarm
    if detected_press2:
        utime.sleep_ms(800)
        if count_press2 > 1:
            print("Editing Alarm")
            alarm_set = False
            editing_alarm = True
        else:
            print("Editing Time")
            clock_set = False
            editing_time = True

        while not clock_set or not alarm_set:
            update_display(None)
            handle_encoder()
            if SW.value() == 0:
                handle_button(SW, 800)
        
        # Reset state variables
        editing_time = False
        editing_alarm = False
        detected_press2 = False
        count_press2 = 0
        return True
    else:
        return False

def handle_encoder():
    global previousValue, hour, minute, setting_minutes, clock, setting_channel, frequency, decimal, setting_integer_part
    
    current_value = CLK_Pin.value()
    if current_value != previousValue:
        if CLK_Pin.value() == 0:
            if setting_channel:
                if setting_integer_part:
                    if DT_Pin.value() == 0:
                        frequency = (frequency - 1) if frequency > 88 else 108
                    else:
                        frequency = (frequency + 1) if frequency < 108 else 88
                else:
                    if DT_Pin.value() == 0:
                        decimal = (decimal - 1) % 10
                    else:
                        decimal = (decimal + 1) % 10
            else:
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
    global last_button_press_time, setting_minutes, clock_set, alarm_set, editing_time, editing_alarm, setting_channel, setting_integer_part
    current_time = utime.ticks_ms()
    if current_time - last_button_press_time > delay:  # Debounce the button
        last_button_press_time = current_time
        if setting_channel:
            if setting_integer_part:
                setting_integer_part = False  # Switch to setting the decimal part
            else:
                fm_radio.SetFrequency(frequency + decimal * 0.1)
                fm_radio.ProgramRadio()
                setting_channel = False  # Exit channel setting mode
                setting_integer_part = True  # Reset for future channel settings
        elif not clock_set:
            if setting_minutes:
                clock.set_time(hour, minute)
                clock_set = True
            setting_minutes = not setting_minutes
        elif not alarm_set:
            if setting_minutes:
                alarm.set_alarm(hour, minute)
                alarm_set = True
            setting_minutes = not setting_minutes
        else:
            # Toggle mute
            new_mute_state = not fm_radio.Mute
            if fm_radio.SetMute(int(new_mute_state)):
                fm_radio.ProgramRadio()
                print("Mute Toggled to:", new_mute_state)
        update_display(None)  # Update display immediately after handling button

def cleanup():
    fm_radio.SetMute(True)
    fm_radio.ProgramRadio()
    alarm.be_quiet()
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
    elif not alarm_set:
        display_time = f"{hour:02}:{minute:02}"
        # Flash the digits while setting the alarm
        if int(utime.time() * (2/3)) % 2:
            if setting_minutes:
                display_time = f"{hour:02}:  "
            else:
                display_time = f"  :{minute:02}"
        oled.text("Set Alarm:", 0, 0)
        text_width = 8 * len(display_time)  # Calculate coordinates to center the text
        x = (SCREEN_WIDTH - text_width) // 2
        y = (SCREEN_HEIGHT - 8) // 2
        oled.text(display_time, x, y)
    elif setting_channel:
        display_channel = f"{frequency}.{decimal}"
        # Flash the digits while setting the channel
        if int(utime.time() * (2/3)) % 2:
            if setting_integer_part:
                display_channel = f"{frequency}. "
            else:
                display_channel = f"   .{decimal}"
        oled.text("Set Channel:", 0, 0)
        text_width = 8 * len(display_channel)  # Calculate coordinates to center the text
        x = (SCREEN_WIDTH - text_width) // 2
        y = (SCREEN_HEIGHT - 8) // 2
        oled.text(display_channel, x, y)
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

# Global variables for setting time, alarm, and channel
hour = 0
minute = 0
frequency = 101
decimal = 9
setting_minutes = False
clock_set = False
alarm_set = False
editing_time = False
editing_alarm = False

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
button1.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed1)
button2.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed2)
button3.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed3)
button4.irq(trigger=Pin.IRQ_FALLING, handler=alarm.snooze_or_stop)

try:
    while True:
        handle_encoder()
        alarm.check_alarm()  # Check if it's time to sound the alarm
        if SW.value() == 0:
            handle_button(SW, 800)
            utime.sleep(0.1)  # Reduce frequency of main loop
        edit_time_or_alarm()
except KeyboardInterrupt:
    cleanup()
    print("Program interrupted and cleaned up")
