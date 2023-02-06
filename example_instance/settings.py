# System setting

from machine import Pin, SPI

class Settings:
    def __init__(self,debug=False):
        self.debug = debug
        
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
        self.bmx_0_cal_data = self.calibration_data(self.bmx_0_name)
        self.bmx_0_temp_scale = 'f'
        
        # indoor BMX settings
        self.bmx_1_bus_id=0
        self.bmx_1_scl_pin=1
        self.bmx_1_sda_pin=0
        self.bmx_1_name = "Indoor"
        self.bmx_1_cal_data = self.calibration_data(self.bmx_1_name)
        self.bmx_1_temp_scale = 'f'
            
            
    def calibration_data(self,name):
        """Return the calibration data for the specified sensor
            
            A dict containing a list of tuples for each sensor.
            The tuples are organized as:
                0: Raw Sensor temperature
                1: Observed (actual) temperature
                
            The tuples may be in any order but the tempurature values
            must use the same scale as the sensor (f or c)
            
        """
        
        l = {
            'Indoor': [
                (68.2, 65.0),
                (70.2, 66.4),
                (71.6, 66.9),
                (72.3, 68.5),
                (73.0, 67.8),
                (73.6, 68.9),
                (68.5, 65.5),
                ],
            'Outdoor': [
                (37.2, 35.4),
                (46.6, 45.3),
                (43.8, 40.1),
                (51.8, 50.4),
                (53.8, 53.1),
                (57.2, 56.3),
                ],
            }

        return l[name]
        
settings = Settings()
