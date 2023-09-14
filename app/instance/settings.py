# System setting

from machine import Pin, SPI
import time
from instance.calibration import calibration_data

class Settings:
    def __init__(self,debug=False):
        self.debug = debug
        # time zone info to adjust UTC time to local time
        self.time_zone_offset = -8 # the adjustment for standard time
        self.daylight_saving_periods = []
        self.daylight_period_setup()
        
        # display spi setup
        self.spi = SPI(0,
            sck=Pin(2),
            miso=Pin(4),
            mosi=Pin(3),
                    )

        self.display_dc = 6
        self.display_cs = 5
        self.display_rst = 7
        
        # outdoor BMX settings
        self.bmx_0_bus_id=1
        self.bmx_0_scl_pin=19
        self.bmx_0_sda_pin=18
        self.bmx_0_name = "Outdoor"
        self.bmx_0_sensor_id = 2
        self.bmx_0_cal_data = calibration_data(self.bmx_0_name)
        self.bmx_0_temp_scale = 'f'
        
        # indoor BMX settings
        self.bmx_1_bus_id=0
        self.bmx_1_scl_pin=1
        self.bmx_1_sda_pin=0
        self.bmx_1_name = "Indoor"
        self.bmx_1_sensor_id = 1
        self.bmx_1_cal_data = calibration_data(self.bmx_1_name)
        self.bmx_1_temp_scale = 'f'
        
        #URL for reporting results
        self.temp_center_url = 'http://10.0.1.4:5000/api/add_reading'
#         self.temp_center_url = 'https://tc.williesworkshop.net/api/add_reading'
            
            
    
    
    def daylight_period_setup(self):
    # U.S. daylight savings time default

        # for 2023
        #DTS begins Sunday, March 12, 2023, 2:00:00 am
        #DTS ends Sunday, November 5, 2023, 2:00:00 am
        self.daylight_saving_periods.append((
            (time.mktime((2023,3,12,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            (time.mktime((2023,11,5,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            ))
        # for 2024
        #DTS begins Sunday, March 10, 2024, 2:00:00 am
        #DTS ends Sunday, November 3, 2024, 2:00:00 am
        self.daylight_saving_periods.append((
            (time.mktime((2024,3,10,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            (time.mktime((2024,11,3,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            ))
        # for 2025
        #DTS begins Sunday, March 9, 2025, 2:00:00 am
        #DTS ends Sunday, November 2, 2025, 2:00:00 am
        self.daylight_saving_periods.append((
            (time.mktime((2025,3,9,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            (time.mktime((2025,11,2,2,0,0,0,0)) + (3600 * self.time_zone_offset)),
            ))

    @property
    def is_daylight_savings(self):
        # Return True if it is daylight savings time else false
        time_seconds = time.mktime(time.localtime())
        
        # check if we are in daylight savings time
        for period in self.daylight_saving_periods:
            if time_seconds >= period[0] and time_seconds <= period[1]:
                # this is the correct period, adjust the time
                return True
        
        return False

        
settings = Settings()

