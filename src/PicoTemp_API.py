from machine import ADC


# returns the temperature value from the onboard sensor
class Temperature:
    def __init__(self):
        adcpin = 4
        self.sensor = ADC(adcpin)

    def read_temp(self):
        adc_value = self.sensor.read_u16()
        volt = (3.3/65535)*adc_value
        temperature = 27 - (volt-0.706)/0.001721
        return round(temperature,1) #returns a truncated value of temperature, type 'float'
