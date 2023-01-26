"""
A class to communicate with the BMX temperature/pressure
sensor
"""

from bmx280_bl import BMX280

class BMX:
    
    def __init__(self,
                 scl_pin=1,
                 sda_pin=0,
                 freq=100000,
                 bus_id=None,
                 name="Unknown BMX",
                 temp_adjust=0,
                 press_adjust=0,
                 ):
        
        self.bmx = None
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.freq = freq
        self.bus_id = bus_id
        self.name=name
        self.temp_adjust = temp_adjust
        self._saved_temp = 0
        self.press_adjust = press_adjust
        self._saved_press = 0
        
        self.bmx = BMX280(
            bus_id=self.bus_id,
            scl=self.scl_pin,
            sda=self.sda_pin,
            freq=self.freq,
            )

    def read(self):
        """Get a reading"""
        return {'pres':self.bmx.pressure,'temp':self.bmx.temperature}
        
    @property
    def temperature(self):
        return self.bmx.temperature

    @property
    def adjusted_temperature(self):
        return self.saved_temp + self.temp_adjust
    
    @property
    def saved_temp(self):
        return self._saved_temp / 10
    
    def temp_changed(self):
        # test/save the temp as an int to reduce rounding error
        temp = int(self.temperature * 10)
        if temp != self._saved_temp:
            self._saved_temp = temp
            return True
        return False
    
    def c_to_f(self,temp_c):
        """Convert centigrade to Fahrenheit"""
        return (temp_c * 1.8) + 32

    @property
    def pressure(self):
        return self.bmx.pressure
    
    @property
    def adjusted_pressure(self):
        return self.pressure + self.press_adjust
    
    def mlb_to_ihg(self,mlb):
        """Convert milibars to inches of mercury"""
        
        return mlb * 0.00029529980164712
