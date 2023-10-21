# System setting

from machine import Pin, SPI, SoftSPI
from settings.calibration_data import calibration_data
from instance import instance
import time
from logging import logging as log
import json
import os

class Settings:
    def __init__(self,debug=False):
        self.debug = debug
        self.testing = False
        self.calibration_data = calibration_data
        
        self.device_id = instance.device_id
        self.sensors = instance.sensors
        self.sensor_json_file = '/instance/sensors.json'
        self._host = instance.host # Use to override the default hosts

        # display spi setup
        self.spi = SPI(0,
            sck=Pin(2),
            miso=Pin(4),
            mosi=Pin(3),
                    )
        self.display_dc = 6
        self.display_cs = 5
        self.display_rst = 7
        
        self.set_bmx_list()

    def set_bmx_list(self,sensors=None):
        if sensors is None:
            try:
                with open(self.sensor_json_file,'r') as f:
                    sensors = f.read()
            except:
                pass
            
        if sensors != None and isinstance(sensors,str):
            self.sensors = json.loads(sensors)
        else:
            log.debug(f'Using default sensor settings')
            
        log.debug(f'sensors: {self.sensors}')
        
        self.bmx_list = []
        for x, sensor in enumerate(self.sensors):
            d = {}
            
            if x > 1:
                break
            
            if x == 0:
                d['bus_id']=1
                d['scl_pin']=19
                d['sda_pin']=18
            else:
                d['bus_id']=0
                d['scl_pin']=1
                d['sda_pin']=0
                    
            d['name'] = sensor['name']
            try:
                d['sensor_id'] = int(sensor['id'])
            except:
                d['sensor_id'] = int(sensor['sensor_id'])
            d['scale'] = sensor['scale']
            try:
                d['cal_data'] = self.calibration_data(d['sensor_id'])
            except:
                d['cal_data'] = self.calibration_data(d['name'])

            self.bmx_list.append(d)
            
        # Save the newly loaded sensor info in instance
        if sensors:
            with open(self.sensor_json_file,'w') as f:
                f.write(sensors)
                
                
    @property
    def host(self):
        """Return the host name"""
        if self._host:
            return self._host
        if self.testing:
            return 'http://10.0.1.4:5000'
        else:
            return 'http://tc.williesworkshop.net'


    @property    
    def ota_source_url(self):
        dest = '/api/check_file_version'
        return f'{self.host}{dest}'
    
    
    @property    
    def reading_export_url(self):
        #URL for reporting results
        dest = '/api/add_reading'
        return f'{self.host}{dest}'

    @property    
    def log_export_url(self):
        #URL for reporting results
        dest = '/api/log'
        return f'{self.host}{dest}'

    @property    
    def get_sensor_url(self):
        #URL to get the device configuration info from the host
        dest = '/api/get_sensor_data'
        return f'{self.host}{dest}'


settings = Settings()


