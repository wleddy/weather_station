"""Some utilities for weather station.
Moved here to help improve ota updates"""

from machine import RTC
import json
import gc
gc.enable()

from wifi_connect import connection
if connection.wifi_available:
    import urequests
from display.display import Display
from logging import logging as log
from settings.settings import settings
from bmx import BMX


def get_display():
    display = Display(settings)
    display.debug = False
    display.clear()
    
    display.centered_text("Starting up...",y=25,width=display.MAX_Y)
    
    return display


def get_sensors():
        # create sensor instances
        sensors = [] #make a list
        for sensor in settings.bmx_list:
            try:
                s = BMX(
                        bus_id = sensor['bus_id'],
                        scl_pin = sensor['scl_pin'],
                        sda_pin = sensor['sda_pin'],
                        name = sensor['name'],
                        sensor_id = sensor['sensor_id'],
                        temp_calibration_list = sensor['cal_data'],
                        temp_scale = sensor['scale'],
                        )
                sensors.append(s)
            except Exception as e:
                mes = f"{sensor['name']} sensor Failed"
                log.exception(e,f'{mes}')
                
        return sensors

           
def export_reading(sensor):
    #Send the current temp to the temp_center app
    
    if not connection.wifi_available:
        return
    
    if not connection.isconnected():
        log.debug("Trying to connect for reading export")
        connection.connect()
        time.sleep(2)
    if connection.isconnected():
        
        gc.collect()

        try:
            r = urequests.get("{url}/{sensor_id}/{temp}/{raw_temp}/{scale}/".format(
                        url = settings.reading_export_url,
                        sensor_id=sensor.sensor_id,
                        temp=sensor.adjusted_temperature,
                        raw_temp = sensor.saved_temp,
                        scale=sensor.temp_scale,
                        )
                    )

            log.debug(f"Got response: {r.text}")
            if r.text.upper() != 'OK':
                log.info(f'export_reading result: r.text[0:80]')
                
            del r
            gc.collect()
            
        except Exception as e:
            log.exception(e,f"Export Reading Failed for {sensor.name}: {str(e)}")
            gc.collect()
            
    else:
        log.info("Not Connected")



def hinlow(sensor=None,temp=None):
    """Save and retrieve the highest and lowest temperatures for today
        omitting either sensor or temp will return the current hinlow
        dict from file if file exists
        
        returns a dict of dicts if they exist in file.
        {<sensor_name>:
            {'date','high','low'}
        ...
        }
    """
    
    
    filename = 'hinlow.txt'

    t = RTC().datetime()
    t = f'{t[0]}-{("00"+str(t[1]))[-2:]}-{("00"+str(t[2]))[-2:]}'
        
    hinlow = {}
    
    try:
        with open(filename,'r') as f:
            hinlow = json.loads(f.read())
    except OSError as e:
        hinlow = {}
    except Exception as e:
        log.exception(e,'hinlow: unexpected read error' )
        
    if not isinstance(hinlow,dict ):
        hinlow = {}

    try:
        temp=int(round(temp,0))
    except TypeError as e:
        if temp is not None:
            log.exception(e,'hinlow:  temp is not a number') 
            temp = None
        
    if not sensor or temp is None:
        return hinlow

    if sensor not in hinlow:
         hinlow[sensor] = {}

    if not 'date' in hinlow[sensor]  or hinlow[sensor]['date'] < t:
        hinlow[sensor] = {} # clear
        hinlow[sensor]['date'] = t

    if not 'high' in hinlow[sensor]  or hinlow[sensor]['high'] < temp:
        hinlow[sensor]['high'] = temp
    if not 'low' in hinlow[sensor]  or hinlow[sensor]['low'] > temp:
        hinlow[sensor]['low'] = temp

    try:
        with open(filename,'w') as f:
             f.write(json.dumps(hinlow))
    except Exception as e:
       log.exception(e,'hinlow: Write failed')

    return hinlow
