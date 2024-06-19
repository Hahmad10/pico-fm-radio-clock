from machine import Pin, I2C, SPI
import time, utime

# Requires ssd1306.py (from micropython-lib) saved on the Pico.
from ssd1306 import SSD1306_SPI # OLED driver
import framebuf # frame buffer used by the OLED driver

class Radio:
    
    def __init__( self, NewFrequency, NewVolume, NewMute ):

#
# set the initial values of the radio
#
        self.Volume = 2
        self.Frequency = 88
        self.Mute = False
#
# Update the values with the ones passed in the initialization code
#
        self.SetVolume( NewVolume )
        self.SetFrequency( NewFrequency )
        self.SetMute( NewMute )
        
      
# Initialize I/O pins associated with the radio's I2C interface

        self.i2c_sda = Pin(26)
        self.i2c_scl = Pin(27)

#
# I2C Device ID can be 0 or 1. It must match the wiring. 
#
# The radio is connected to device number 1 of the I2C device
#
        self.i2c_device = 1 
        self.i2c_device_address = 0x10

#
# Array used to configure the radio
#
        self.Settings = bytearray( 8 )


        self.radio_i2c = I2C( self.i2c_device, scl=self.i2c_scl, sda=self.i2c_sda, freq=200000)
        self.ProgramRadio()

    def SetVolume( self, NewVolume ):
#
# Conver t the string into a integer
#
        try:
            NewVolume = int( NewVolume )
            
        except:
            return( False )
        
#
# Validate the type and range check the volume
#
        if ( not isinstance( NewVolume, int )):
            return( False )
        
        if (( NewVolume < 0 ) or ( NewVolume >= 16 )):
            return( False )

        self.Volume = NewVolume
        return( True )



    def SetFrequency( self, NewFrequency ):
#
# Convert the string into a floating point value
#
        try:
            NewFrequency = float( NewFrequency )
            
        except:
            return( False )
#
# validate the type and range check the frequency
#
        if ( not ( isinstance( NewFrequency, float ))):
            return( False )
 
        if (( NewFrequency < 88.0 ) or ( NewFrequency > 108.0 )):
            return( False )

        self.Frequency = NewFrequency
        return( True )
        
    def SetMute( self, NewMute ):
        
        try:
            self.Mute = bool( int( NewMute ))
            
        except:
            return( False )
        
        return( True )

#
# convert the frequency to 10 bit value for the radio chip
#
    def ComputeChannelSetting( self, Frequency ):
        Frequency = int( Frequency * 10 ) - 870
        
        ByteCode = bytearray( 2 )
#
# split the 10 bits into 2 bytes
#
        ByteCode[0] = ( Frequency >> 2 ) & 0xFF
        ByteCode[1] = (( Frequency & 0x03 ) << 6 ) & 0xC0
        return( ByteCode )

#
# Configure the settings array with the mute, frequency and volume settings
#
    def UpdateSettings( self ):
        
        if ( self.Mute ):
            self.Settings[0] = 0x80
        else:
            self.Settings[0] = 0xC0
  
        self.Settings[1] = 0x09 | 0x04
        self.Settings[2:3] = self.ComputeChannelSetting( self.Frequency )
        self.Settings[3] = self.Settings[3] | 0x10
        self.Settings[4] = 0x04
        self.Settings[5] = 0x00
        self.Settings[6] = 0x84
        self.Settings[7] = 0x80 + self.Volume

#        
# Update the settings array and transmitt it to the radio
#
    def ProgramRadio( self ):

        self.UpdateSettings()
        self.radio_i2c.writeto( self.i2c_device_address, self.Settings )

#
# Extract the settings from the radio registers
#
    def GetSettings( self ):
#        
# Need to read the entire register space. This is allow access to the mute and volume settings
# After and address of 255 the 
#
        self.RadioStatus = self.radio_i2c.readfrom( self.i2c_device_address, 256 )

        if (( self.RadioStatus[0xF0] & 0x40 ) != 0x00 ):
            MuteStatus = False
        else:
            MuteStatus = True
            
        VolumeStatus = self.RadioStatus[0xF7] & 0x0F
 
 #
 # Convert the frequency 10 bit count into actual frequency in Mhz
 #
        FrequencyStatus = (( self.RadioStatus[0x00] & 0x03 ) << 8 ) | ( self.RadioStatus[0x01] & 0xFF )
        FrequencyStatus = ( FrequencyStatus * 0.1 ) + 87.0
        
        if (( self.RadioStatus[0x00] & 0x04 ) != 0x00 ):
            StereoStatus = True
        else:
            StereoStatus = False
        
        return( MuteStatus, VolumeStatus, FrequencyStatus, StereoStatus )

#
# initialize the FM radio
#
fm_radio = Radio( 101.9, 2, False )

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
    
    oled.text("FM Radio Menu", 15, 0) # Print the text starting from 0th column and 0th row
    oled.text("1 - change freq", 0, 10) # Menu entry at x=0, y=10
    oled.text("2 - change vol", 0, 20)
    oled.text("3 - mute audio", 0, 30)
    oled.text("4 - current sett", 0, 40)
    oled.text("Count is: %4d" % Count, 0, 50 )
        
#
# Update the text on the screen
#
#     oled.text("FM Radio Clock", 0, 0) # Text at column 0, row 0
#     oled.text("Pico", 45, 10) # Text at x=45, y=10
#     oled.text("Count is: %4d" % Count, 0, 30 ) # Print the value stored in the variable Count. 
#         
#
# Draw box below the text
#
#    oled.rect( 0, 50, 128, 5, 1  )        

#
# Transfer the buffer to the screen
#
    oled.show()


#
# display the menu
#
 
 
 
#     print("")
#     print( "FM Radio Menu" );
#     print("")
#     print( "1 - change radio frequency" )
#     print( "2 - change volume level" )
#     print( "3 - mute audio" )
#     print( "4 - read current settings" )
#     
#     select = input( "Enter menu number > " )

#
# Set radio frequency
#
    if ( select == "1" ):
        Frequency = input( "Enter frequncy in Mhz ( IE 100.3 ) > " )

        if ( fm_radio.SetFrequency( Frequency ) == True ):
            fm_radio.ProgramRadio()
        else:
            print( "Invalid frequency( Range is 88.0 to 108.0 )" )

#
# Set volume level of radio
#
    elif ( select == "2" ):
        Volume = input( "Enter volume level ( 0 to 15, 15 is loud ) > " )
        
        if ( fm_radio.SetVolume( Volume ) == True ):
            fm_radio.ProgramRadio()
        else:
            print( "Invalid volume level( Range is 0 to 15 )" )
        
#        
# Enable mute of radio       
#        
    elif( select == "3" ):
        Mute = input( "Enter mute ( 1 for Mute, 0 for audio ) > " )
        
        if ( fm_radio.SetMute( Mute ) == True ):
            fm_radio.ProgramRadio()
        else:
            print( "Invalid mute setting" )

#
# Display radio current settings
#
    elif( select == "4" ):
        Settings = fm_radio.GetSettings()

        print( Settings )
        print("")
        print("Radio Status")
        print("")

        print( "Mute: ", end="" )
        if ( Settings[0] == True ):
            print( "enabled" )
        else:
            print( "disabled" )

        print( "Volume: %d" % Settings[1] )

        print( "Frequency: %5.1f" % Settings[2] )

        print( "Mode: ", end="" )
        if ( Settings[3] == True ):
            print( "stereo" )
        else:
            print( "mono" )


    else:
        print( "Invalid menu option" )

        



    
    
  

