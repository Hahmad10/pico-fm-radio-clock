from machine import RTC
import utime

class Clock:
    def __init__(self):
        self.rtc = RTC()
        self.rtc.datetime((2024, 7, 9, 2, 22, 0, 0, 0)) # Default time set to 10 PM
        self.time_format_24hr = True
        self.colon_visible = True
        self.last_toggle = utime.ticks_ms() # Track last toggle for half-second flash

    def get_time(self):
        # Check if half a second has passed to toggle the colon
        current_ms = utime.ticks_ms()
        if utime.ticks_diff(current_ms, self.last_toggle) >= 500:
            self.colon_visible = not self.colon_visible
            self.last_toggle = current_ms # Reset the toggle time

        year, month, day, weekday, hour, minute, second, subsecond = self.rtc.datetime()
        colon = ':' if self.colon_visible else ' '
        if self.time_format_24hr:
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

    def toggle_time_format(self):
        self.time_format_24hr = not self.time_format_24hr

    def set_time(self, hour, minute):
        # Retrieve the current date and weekday
        year, month, day, weekday, _, _, _, _ = self.rtc.datetime()
        # Set the new time while keeping the current date
        self.rtc.datetime((year, month, day, weekday, hour, minute, 0, 0))
