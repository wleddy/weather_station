# System setting

from machine import Pin, SPI
from settings.calibration_data import calibration_data
import time

class Settings:
	def __init__(self,debug=False):
		self.debug = debug
		self.testing = False
		self.calibration_data = calibration_data
		
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
		self.bmx_0_cal_data = self.calibration_data(self.bmx_0_name)
		self.bmx_0_temp_scale = 'f'
		
		# indoor BMX settings
		self.bmx_1_bus_id=0
		self.bmx_1_scl_pin=1
		self.bmx_1_sda_pin=0
		self.bmx_1_name = "Indoor"
		self.bmx_1_sensor_id = 1
		self.bmx_1_cal_data = self.calibration_data(self.bmx_1_name)
		self.bmx_1_temp_scale = 'f'
		
	
	@property
	def host(self):
		"""Return the host name"""
		if self.testing:
			return 'http://10.0.1.4:5000'
		else:
			return 'http://tc.williesworkshop.net'


	@property	
	def ota_source_url(self):
		dest = '/api/get_file'
		return f'{self.host}{dest}'
	
	
	@property	
	def reading_export_url(self):
		#URL for reporting results
		dest = '/api/add_reading'
		return f'{self.host}{dest}'
	

		
settings = Settings()
