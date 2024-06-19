from machine import Pin, I2C, SPI
import time, utime
from ssd1306 import SSD1306_SPI
import framebuf

class Radio:
    def __init__(self, NewFrequency, NewVolume, NewMute):
        self.Volume = 2
        self.Frequency = 88
        self.Mute = False
        self.SetVolume(NewVolume)
        self.SetFrequency(NewFrequency)
        self.SetMute(NewMute)

        self.i2c_sda = Pin(26)
        self.i2c_scl = Pin(27)
        self.i2c_device = 1
        self.i2c_device_address = 0x10
        self.Settings = bytearray(8)
        self.radio_i2c = I2C(self.i2c_device, scl=self.i2c_scl, sda=self.i2c_sda, freq=200000)
        self.ProgramRadio()

    def SetVolume(self, NewVolume):
        try:
            NewVolume = int(NewVolume)
        except:
            return False
        if not isinstance(NewVolume, int):
            return False
        if NewVolume < 0 or NewVolume >= 16:
            return False
        self.Volume = NewVolume
        return True

    def SetFrequency(self, NewFrequency):
        try:
            NewFrequency = float(NewFrequency)
        except:
            return False
        if not isinstance(NewFrequency, float):
            return False
        if NewFrequency < 88.0 or NewFrequency > 108.0:
            return False
        self.Frequency = NewFrequency
        return True

    def SetMute(self, NewMute):
        try:
            self.Mute = bool(int(NewMute))
        except:
            return False
        return True

    def ComputeChannelSetting(self, Frequency):
        Frequency = int(Frequency * 10) - 870
        ByteCode = bytearray(2)
        ByteCode[0] = (Frequency >> 2) & 0xFF
        ByteCode[1] = ((Frequency & 0x03) << 6) & 0xC0
        return ByteCode

    def UpdateSettings(self):
        self.Settings[0] = 0x80 if self.Mute else 0xC0
        self.Settings[1] = 0x09 | 0x04
        self.Settings[2:3] = self.ComputeChannelSetting(self.Frequency)
        self.Settings[3] = self.Settings[3] | 0x10
        self.Settings[4] = 0x04
        self.Settings[5] = 0x00
        self.Settings[6] = 0x84
        self.Settings[7] = 0x80 + self.Volume

    def ProgramRadio(self):
        self.UpdateSettings()
        self.radio_i2c.writeto(self.i2c_device_address, self.Settings)

    def GetSettings(self):
        self.RadioStatus = self.radio_i2c.readfrom(self.i2c_device_address, 256)
        MuteStatus = False if (self.RadioStatus[0xF0] & 0x40) != 0x00 else True
        VolumeStatus = self.RadioStatus[0xF7] & 0x0F
        FrequencyStatus = ((self.RadioStatus[0x00] & 0x03) << 8) | (self.RadioStatus[0x01] & 0xFF)
        FrequencyStatus = (FrequencyStatus * 0.1) + 87.0
        StereoStatus = True if (self.RadioStatus[0x00] & 0x04) != 0x00 else False
        return MuteStatus, VolumeStatus, FrequencyStatus, StereoStatus

# initialize the FM radio
fm_radio = Radio(107.3, 2, False)

Count = 0
Last_press = 0
Pressed = False
button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)

def Button_Pressed(button):
    global Count, Last_press
    new_time = utime.ticks_ms()
    if (new_time - Last_press) > 50:
        Pressed = True
        if Count < 4:
            Count += 1
            Last_press = new_time
        else:
            Count = 0
            Count += 1
            Last_press = new_time

button.irq(trigger=machine.Pin.IRQ_FALLING, handler=Button_Pressed)

# Define columns and rows of the oled display
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

# Initialize I/O pins associated with the oled display SPI interface
spi_sck = Pin(18)
spi_sda = Pin(19)
spi_res = Pin(21)
spi_dc = Pin(20)
spi_cs = Pin(17)

SPI_DEVICE = 0
oled_spi = SPI(SPI_DEVICE, baudrate=100000, sck=spi_sck, mosi=spi_sda)
oled = SSD1306_SPI(SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True)

def display_update(message):
    oled.fill(0)
    oled.text(message, 0, 30)
    oled.show()
    time.sleep(3)

def display_menu():
    oled.fill(0)
    oled.text("FM Radio Menu", 15, 0)
    oled.text("1 - change freq", 0, 10)
    oled.text("2 - change vol", 0, 20)
    oled.text("3 - mute audio", 0, 30)
    oled.text("4 - current sett", 0, 40)
    oled.show()

while True:
    display_menu()    
    
    start_time = utime.ticks_ms()
    
    # Wait for 5 seconds to detect button presses
    while utime.ticks_diff(utime.ticks_ms(), start_time) < 5000:
        time.sleep(0.5)

        if Count == 1:
            display_update("Enter freq in MHz")
            Frequency = input("Enter frequency in MHz (IE 100.3) > ")
            if fm_radio.SetFrequency(Frequency):
                fm_radio.ProgramRadio()
                display_update(f"Freq: {Frequency} MHz")
            else:
                print("Invalid frequency (Range is 88.0 to 108.0)")

        elif Count == 2:
            display_update("Enter volume level")
            Volume = input("Enter volume level (0 to 15, 15 is loud) > ")
            while (fm_radio.SetVolume(Volume)==False):
                display_update("Range is 0 to 15!")
                print("Invalid volume level (Range is 0 to 15)")
                display_update("Enter volume level")
                Volume = input("Enter volume level (0 to 15, 15 is loud) > ")
            fm_radio.ProgramRadio()
            display_update(f"Volume: {Volume}")

        elif Count == 3:
            display_update("1 for Mute, 0 for audio")
            Mute = input("Enter mute (1 for Mute, 0 for audio) > ")
            if fm_radio.SetMute(Mute):
                fm_radio.ProgramRadio()
                display_update(f"Mute: {'enabled' if Mute == '1' else 'disabled'}")
            else:
                display_update("Invalid mute setting")
                print("Invalid mute setting")

        elif Count == 4:
            display_update("Settings displayed in Shell")
            Settings = fm_radio.GetSettings()
            print(Settings)
            print("\nRadio Status\n")
            print(f"Mute: {'enabled' if Settings[0] else 'disabled'}")
            print(f"Volume: {Settings[1]}")
            print(f"Frequency: {Settings[2]:.1f}")
            print(f"Mode: {'stereo' if Settings[3] else 'mono'}")
            

        else:
            print("Invalid menu option")

        Count = 0  # reset button press count
        Pressed = False
