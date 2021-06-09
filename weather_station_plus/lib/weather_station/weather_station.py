"""Classes to interact with the BMP sensor and display the readings"""

import json
from machine import Pin, deepsleep
import utime as time

from bmx280_bl import BMX280
from ssd1306_display import ssd1306_i2c_bl

from lora.lora_config import * #import the pin configuration
from lora.sx127x import SX127x
from spi_setup.spi_setup import get_spi
from setup import setup

from ili9341 import color565
from xglcd_font import XglcdFont

class LoRaRadio:
    def __init__(self):
        spi,ss = get_spi('ttgo') 
        self.lora = SX127x(spi,ss,pins=device_config, parameters=lora_parameters)
        #self.lora.set_spreading_factor(6)
        
    def send(self,payload=None):
        if payload:
            self.lora.println(payload)
            
            
    def receive(self,timeout=10):
        """Wait for something over the radio
        Wait timeout seconds for a response or forever if not timeout
        """
        
        timer = None if not timeout else timeout + time.time()
        
        def time_remaining():
            if timer == None:
                return True
            if timer - time.time() > 0:
                return True
            
            return False
        
        while time_remaining():
            if self.lora.received_packet():
                payload = self.lora.read_payload()
                return payload
                break
 
        return None


class WeatherSensor:
    """Remote tempurature and pressure sensor

    Using BMP sensor to get reading and communicate to weather
    station receiver via LoRa radio
    """
    
    def __init__(self,sensor_name,scl_pin=15,sda_pin=4,power_pin=17):
        
        self.name = str(sensor_name).strip()
        self.sensor_power = Pin(power_pin,Pin.OUT)
        self.on() # sensor_power required to initialize object
        
        self.bmx = BMX280(scl=scl_pin,sda=sda_pin)
        self.off() 
        
    
    def read(self):
        """Get a reading"""
        self.on()       
        return {'name':self.name,'pres':self.bmx.pressure,'temp':self.bmx.temperature}
    
    
    def on(self):
        """Power up the sensor

        The sensor must remained powered up if any other devices
        are attempting to use the same I2C bus
        """
        self.sensor_power.on()
        time.sleep(.5)
        
        
    def off(self):
        """Power down the sensor"""
        
        self.sensor_power.off()
        

class WeatherReader:
    """Get a weather reading from WeatherSendor and display it on the
    built-in oled screen
    """
    
    def __init__(self,scl_pin=15,sda_pin=4):
        # connect to display
        self.oled = ssd1306_i2c_bl.Display(scl_pin_id=scl_pin,sda_pin_id=sda_pin)
        
        
    def display(self,txt,x=0,y=0,show=True,clear=False):
        self.oled.show_text(str(txt),x,y,clear_first=clear,show_now=show)

    def display_clear(self):
        self.oled.clear()


    def c_to_f(self,temp_c):
        """Convert centigrade to Fahrenheit"""
        
        return temp_c * 9 / 5 + 32

    def mlb_to_ihg(self,mlb):
        """Convert milibars to inches of mercury"""
        
        return mlb * 0.00029529980164712
    

def start_sensor(name='Unknown',sleep_seconds=60):
    sensor = WeatherSensor(name)
    radio = LoRaRadio()
    
    while True:
        readings = None
        try:
            readings = sensor.read() # sensor is now turned on...
            sensor.off()
            if valid_reading(readings):
                radio.send(json.dumps(readings))
                
                # there seems to be an issue with Thonny reconnecting
                #   to the mpu when in deepsleep, so just give me a few
                #   seconds to break out.
                time.sleep(5)
                
                break # exit to deepsleep
            else:
                print(readings)
        except Exception as e:
            print("reading Error: {}".format(str(e)))
        
        time.sleep(5) # loop till sthere is a reading
        
    deepsleep(sleep_seconds * 1000) # time is millis
        
        
def start_receiver():
    radio = LoRaRadio()
    reader = WeatherReader()
    reader.display("Ready to receive",clear=True)
    
    spi, display = setup()
    RED = color565(255,0,0)
    DEFAULT_FONT = XglcdFont(
        '/lib/fonts/EspressoDolce18x24.c',
        18,
        24,
    )
    
    
    display.draw_text(0, 0, 'Waiting...', DEFAULT_FONT, RED)

    while True:
        readings = radio.receive(timeout=5)
        if readings:
            try:
                readings = json.loads(readings.decode("utf-8"))
                print(readings)   
                if valid_reading(readings):
                    # display on TFT display
                    display.clear()
                    display.draw_text(0, 0, "Station: {}".format(readings['name']), DEFAULT_FONT, RED)
                    display.draw_text(0, 24, "Press: {}".format(round(reader.mlb_to_ihg(readings['pres']),2)), DEFAULT_FONT, RED)
                    display.draw_text(0, 48, "Temp: {0:.1f}".format(int(reader.c_to_f(readings['temp'])*10)/10), DEFAULT_FONT, RED)
                    
                    # display on builtin display
                    reader.display("Station: {}".format(readings['name']),clear=True,show=False)
                    reader.display("Press: {}".format(round(reader.mlb_to_ihg(readings['pres']),2)),y=14,show=False)
                    reader.display("Temp: {0:.1f}".format(int(reader.c_to_f(readings['temp'])*10)/10),y=28,show=True)
                else:
                    reader.display("bad response",clear=True)
            except Exception as e:
                reader.display("Error: {}".format(e),clear=True,show=True)
                print(e)
                        
        time.sleep(5)
                            

def valid_reading(readings):
    try:
        if readings and 'name' in readings and 'temp' in readings and 'pres' in readings:
            return True
    except:
        print(readings)
        pass
    
    return False

