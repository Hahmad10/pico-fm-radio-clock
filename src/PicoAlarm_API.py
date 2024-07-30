from machine import Pin, PWM
import utime

class Alarm:
    def __init__(self, buzzer_pin, snooze_pin, radio):
        self.buzzer = PWM(Pin(buzzer_pin))
        self.snooze_pin = Pin(snooze_pin, Pin.IN, Pin.PULL_DOWN)
        self.snooze_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.snooze_or_stop)
        self.alarm_time = None
        self.alarm_active = False
        self.snooze_duration = 10 # Default snooze duration in seconds
        self.snooze_active = False
        self.last_snooze_time = None
        self.snooze_pressed_time = 0
        self.was_radio_playing = False # Flag to track radio state
        self.fm_radio = radio # Store the fm_radio object

    def set_alarm(self, hour, minute):
        self.alarm_time = (hour, minute)
        self.alarm_active = True
        print(f"Alarm set for {hour:02}:{minute:02}")

    def set_snooze_duration(self, duration):
        self.snooze_duration = duration
        print(f"Snooze duration set to {self.snooze_duration} seconds")

    def check_alarm(self):
        if self.alarm_active and not self.snooze_active:
            current_time = utime.localtime()
            if (current_time[3], current_time[4]) == self.alarm_time:
                self.sound_alarm()

        if self.snooze_active:
            current_time = utime.time()
            if current_time - self.last_snooze_time >= self.snooze_duration:
                self.sound_alarm()

    def sound_alarm(self):
        # Mute the radio if it's playing
        if not self.fm_radio.Mute:
            self.was_radio_playing = True
            self.fm_radio.SetMute(True)
            self.fm_radio.ProgramRadio()
        else:
            self.was_radio_playing = False
        self.alarm_active = False
        print("Alarm sounding")
        self.snooze_active = False

        while not self.snooze_active:
            self.play_tone(1500)
            utime.sleep(0.25)
            self.be_quiet()
            utime.sleep(0.25)

    def play_tone(self, frequency):
        self.buzzer.duty_u16(30000)     # volume
        self.buzzer.freq(frequency)

    def be_quiet(self):
        self.buzzer.duty_u16(0)

    def snooze_or_stop(self, pin):
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time, self.snooze_pressed_time) > 500:   # Debounce
            if not self.snooze_active:
                print("Alarm snoozed")
                self.snooze_active = True
                self.last_snooze_time = utime.time()
                self.be_quiet()
            else:
                print("Alarm stopped")
                self.alarm_active = False
                self.snooze_active = False
                self.be_quiet()
            self.snooze_pressed_time = current_time
            if self.was_radio_playing:
                self.fm_radio.SetMute(False)
                self.fm_radio.ProgramRadio()
