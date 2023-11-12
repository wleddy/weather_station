# System setting

from machine import Pin, SPI, SoftSPI
from instance import instance
from logging import logging as log
from wifi_connect import connection
if connection.wifi_available:
    import urequests
    
import json
import os
import time

class Settings:
    def __init__(self,debug=False):
        self.debug = debug
        self.device_id = instance.device_id
        self.host = instance.host
        utc = -8
        try:
            utc = instance.UTC_offset
        except:
            pass
            
        self.UTC_offset = utc
                    
        self.sensor_json_file = '/instance/sensors.json'
        self.calibration_json_file = '/instance/calibration_data.json'

        # display spi setup
        self.spi = SPI(0,
            sck=Pin(2),
            miso=Pin(4),
            mosi=Pin(3),
                    )
        self.display_dc = 6
        self.display_cs = 5
        self.display_rst = 7
        
       
    @property
    def bmx_list(self):
        sensors = None
        # get the sensor data from the host
        try:
            if connection.is_connected():
                r = urequests.get(f'{settings.get_sensor_url}/{settings.device_id}')
                if r.status_code == 200 and r.text:
                    sensors = r.text
                    with open(self.sensor_json_file,'w') as fp:
                        fp.write(sensors)
                    
        except Exception as e:
            log.exception(e,'Unable to get sensor data from host')
        
        if sensors is None:
            try:
                with open(self.sensor_json_file,'r') as f:
                    sensors = f.read()
            except:
                pass
            
           
        if sensors != None and isinstance(sensors,str):
            sensors = json.loads(sensors)
        else:
            log.error('sensor data not of string type')

        if sensors is None:
            # if No connection is available, subsitute some default sensor data
            log.info('Using default sensor data')
            sensors = []
                    
        bmx_list = []
        for x, sensor in enumerate(sensors):
            d = {}
            
            if x > 1:
                # we can only handle 2 sensors at most
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
            d['sensor_id'] = int(sensor['id'])
            d['scale'] = sensor['scale']
            
            try:
                d['cal_data'] = self.calibration_data[str(d['sensor_id'])]
            except Exception as e:
                d['cal_data'] = []
                log.exception(e,f'Calibration failed with sensor id {d["sensor_id"]}')                   
                
            bmx_list.append(d)
           
        log.debug(f'bmx_list: {bmx_list}')
        
        return bmx_list
        
            
    @property
    def calibration_data(self):
        cal_data=None
        # get the sensor data from the host
        try:
            if connection.is_connected():
                r = urequests.get(f'{settings.get_calibration_url}/{settings.device_id}')
                if r.status_code == 200 and r.text:
                    cal_data = r.text
        except Exception as e:
            log.exception(e,'Unable to get calibration data from host')
        
        if cal_data == None:
            try:
                with open(self.calibration_json_file,'r') as f:
                    cal_data = f.read()
            except:
                pass
            
        if cal_data != None:
            if isinstance(cal_data,str):
                cal_data = json.loads(cal_data)
            elif isinstance(cal_data,dict):
                cal_data = cal_data
                
            with open(self.calibration_json_file,'w') as f:
                f.write(json.dumps(cal_data))
            
        elif not cal_data:
            cal_data = {} # no correction
            log.debug('No Calibration Data')
        else:
            log.debug('Using default calibration settings')
            
        log.debug(f'calibration data: {cal_data}')
 
        return cal_data
        
        
    @property    
    def ota_source_url(self):
        dest = '/api/get_file'
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
