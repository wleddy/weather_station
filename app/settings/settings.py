# System setting

from machine import Pin, SPI, SoftSPI
from instance import instance
import time
from logging import logging as log
import json
import os

class Settings:
    def __init__(self,debug=False):
        self.debug = debug
        self.testing = False        
        self.device_id = instance.device_id
            
        self.calibration_data = {}

        self.sensors = instance.sensors
        self.sensor_json_file = '/instance/sensors.json'
        self.calibration_json_file = '/instance/calibration_data.json'
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
                    
        self.set_calibration_data()

        self.bmx_list = []
        for x, sensor in enumerate(self.sensors):
            d = {}
            
            if x > 1:
                break
            
            # I2C Setup
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
                d['cal_data'] = self.calibration_data[str(d['sensor_id'])]
            except Exception as e:
                d['cal_data'] = []
                log.info()
                log.exception(e,f'Calibration failed with sensor id {d["sensor_id"]}')                   

            self.bmx_list.append(d)
           
        log.debug(f'bmx_list: {self.bmx_list}')

        # Save the newly loaded sensor info in instance
        if sensors:
            with open(self.sensor_json_file,'w') as f:
                f.write(sensors)
       
       
    def set_calibration_data(self,cal_data=None):
        if cal_data == None:
            try:
                with open(self.calibration_json_file,'r') as f:
                    cal_data = f.read()
            except:
                pass
            
        if cal_data != None:
            if isinstance(cal_data,str):
                self.calibration_data = json.loads(cal_data)
            elif isinstance(cal_data,dict):
                self.calibration_data = cal_data
                
            with open(self.calibration_json_file,'w') as f:
                f.write(json.dumps(self.calibration_data))
            
        elif not cal_data and not self.calibration_data:
            self.calibration_data = {} # no correction
            log.debug('No Calibration Data')
        else:
            log.debug('Using default calibration settings')
            
        log.debug(f'calibration data: {self.calibration_data}')
 
        
        
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

    @property    
    def get_calibration_url(self):
        #URL to get the device configuration info from the host
        dest = '/api/get_calibration_data'
        return f'{self.host}{dest}'

settings = Settings()
