"""
A class to communicate with the BMX temperature/pressure
sensor
"""

from bmx280_bl import BMX280
from settings.settings import settings
from logging import logging as log

class BMX:
    
    def __init__(self,
                 scl_pin=1,
                 sda_pin=0,
                 freq=100000,
                 bus_id=None,
                 name="Unknown BMX",
                 sensor_id=0,
                 temp_calibration_list=[],
                 press_adjust=0,
                 temp_scale="f", # f or c
                 ):
        
        self.bmx = None
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.freq = freq
        self.bus_id = bus_id
        self.name=name
        self.sensor_id = sensor_id
        self.temp_scale = str(temp_scale).lower().strip()
        self.temp_calibration_list = temp_calibration_list
        if not isinstance(self.temp_calibration_list,list):
            self.temp_calibration_list = []
        else:
            self.temp_calibration_list.sort()
            
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
        return self.saved_temp * self.calibration_factor
    
   
#     @property
#     def calibration_factor(self):
#         """Return the calibation factor based on self.saved_temp
#             tuple order is (raw sensor temp, observed temp)
#         """
#         c = None
#         if len(self.temp_calibration_list) > 0:
# #             print(self.temp_calibration_list)
#             s = self.saved_temp
#             low_value = (s,s)
#             high_value = (s,s)
#
#             for t in self.temp_calibration_list:
#                 if t[0] <= s and t[0] <= low_value[0]:
#                     low_value = t
#                 if t[0] >= s or t[0] >= high_value[0]:
#                     high_value = t
#
#             # get the average of the raw temps and the observed temps
#             raw = (low_value[0] + high_value[0]) / 2
#             observed = (low_value[1] + high_value[1]) / 2
#             c = (raw,observed)
#
#         if not c:
#             return 1 # No correction
#         else:
# #             if settings.debug:
# #                 print("c",c,"low",low_value,"high",high_value)
# #                 print("{} Calibration: {}:{} = {:.3f}".format(self.name,str(low_value),str(high_value),c[1]/c[0]))
#
#             # add a bit to avoid div by 0 error
#             return round(c[1]/(c[0] + 0.00001),2)

    @property
    def calibration_factor(self):
        """Return the calibation factor based on self.saved_temp
            tuple order is (raw sensor temp, observed temp)
        """
        out = None
        if self.temp_scale == "f":
            temp = self.c_to_f(self.temperature)
        else:
            temp =  self.temperature
            

        log.debug(f'{self.name} temp: {temp}')
        hi_temp = temp
        lo_temp = temp
        hi_obs = hi_temp
        lo_obs = lo_temp
        if len(self.temp_calibration_list) > 0:
            if lo_temp <= self.temp_calibration_list[0][0]:
                hi_obs = lo_obs = self.temp_calibration_list[0][1]
                hi_temp = lo_temp = self.temp_calibration_list[0][0]
            else:
                for i in range(len(self.temp_calibration_list)):
                    r,o = self.temp_calibration_list[i]
                    hi_obs = o
                    hi_temp = r
                    if temp <= r:
                        break
                    else:
                        lo_obs = o
                        lo_temp = r

            log.debug(f'low: {lo_temp}/{lo_obs}, hi: {hi_temp}/{hi_obs}')
            out = ((hi_obs/(hi_temp + 0.00001)) + (lo_obs/(lo_temp + 0.00001))) / 2
            log.debug(f'adj. factor: {out}')
        if out is None:
            return 1 # No correction
        else:
            return round(out,2)

 
    @property
    def saved_temp(self):
        if self.temp_scale == "f":
            temp = self.c_to_f(self._saved_temp / 10)
        else:
            temp =  self._saved_temp / 10
            
        return round(temp,2,)
    
    def temp_changed(self):
        # test/save the temp as an int to reduce rounding error
        temp = int(round(self.temperature,2) * 10)
        if temp != self._saved_temp:
            self._saved_temp = temp
            return True
        return False
    
    def c_to_f(self,temp_c):
        """Convert centigrade to Fahrenheit"""
        return (temp_c * 1.8) + 32
    
    def f_to_c(self,temp_f):
        """Convert fahrenheit to centigrade"""
        return (temp_f - 32) / 1.8

    @property
    def pressure(self):
        return self.bmx.pressure
    
    @property
    def adjusted_pressure(self):
        return self.pressure + self.press_adjust
    
    def mlb_to_ihg(self,mlb):
        """Convert milibars to inches of mercury"""
        
        return mlb * 0.00029529980164712


if __name__ == '__main__':
    bmx = BMX()
    bmx.temp_calibration_list = [[60.1, 58], [64, 62], [65, 64], [66, 65], [75.8, 73.4], [77.9, 80]]
#     print(bmx.c_to_f(bmx.temperature))
    for temp in [50,60,70,80]:
        print(f'temp: {temp}')
        print(bmx.calibration_factor(temp))
        print(f'result: {temp * bmx.calibration_factor(temp)}')
