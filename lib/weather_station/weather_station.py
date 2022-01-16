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

# from ili9341 import color565, Display
from display.display import Display, Button
# from xglcd_font import XglcdFont

ROW_HEIGHT = 109 # height of each row in display

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

    Using BMP sensor to get reading
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
        
    
    def c_to_f(self,temp_c):
        """Convert centigrade to Fahrenheit"""
        
        return (temp_c * 1.8) + 32

    
    def mlb_to_ihg(self,mlb):
        """Convert milibars to inches of mercury"""
        
        return mlb * 0.00029529980164712
    

class WeatherDisplay:
    """Use the built-in oled screen
    """
    
    def __init__(self,scl_pin=15,sda_pin=4):
        # connect to display
        self.oled = ssd1306_i2c_bl.Display(scl_pin_id=scl_pin,sda_pin_id=sda_pin)
        
        
    def display(self,txt,x=0,y=0,show=True,clear=False):
        self.oled.show_text(str(txt),x,y,clear_first=clear,show_now=show)

    def display_clear(self):
        self.oled.clear()
    

def start_sensor(name='Unknown',sleep_seconds=0,**kwargs):
    sensor = WeatherSensor(name)
    radio = LoRaRadio()
    
    # the sensor power must be on or the I2C bus won't work
    #   and the display operations will fail
    sensor.on()
    display = None
    if sleep_seconds == 0:
        #use the builtin display
#         display = WeatherDisplay()
#         display.display("Starting up...",clear=True)
        display = get_display()
        
    t_adjust = kwargs.get("t_adjust",0) # temperature correction in C
    print("manual temp correction: ",t_adjust)
    
    remote_row = 10
    local_row = remote_row + ROW_HEIGHT
    last_remote = None # retain the last remote reading
    remote_no_response_limit = 10 # Report lost contact after this many failed attempts to receive
    receive_attempts = 0
    receiver_timeout = 5 # don't wait too long the first time
    
    l_temp_save = None
    r_temp_save = None
    
    while True:
        try:
            local = sensor.read() # sensor is now turned on...
            local["temp"] += t_adjust # apply manual correction
            print("adjusted local: ",local)
        except:
            local = None
        
        try:
            remote = radio.receive(timeout=receiver_timeout)
            print("received: ",remote)

            if not valid_reading(remote):
                remote = last_remote
                receive_attempts += 1
#                 print("Attempts:",receive_attempts)
            else:
                last_remote = remote
                receive_attempts = 0
                
        except:
            remote = last_remote
            
        if remote:
            remote = json.loads(remote.decode("utf-8"))

        if sleep_seconds == 0:
            # wait longer to recive report after first pass but
            #   only if this is the local device
            receiver_timeout = 20 
            
        l_temp = r_temp = "?"
#         l_pres = r_pres = pres_string("?")
        local_name = "Local"
        remote_name = "Remote"
        if local:
            radio.send(json.dumps(local))
#             l_temp = temp_string("{:.1f}".format(round(sensor.c_to_f(local["temp"]),1)))
#             l_pres = pres_string("{:.2f}".format(round(sensor.mlb_to_ihg(local["pres"]),2)))
            l_temp = "{:.1f}".format(round(sensor.c_to_f(local["temp"]),1))
            local_name = local["name"]
        if receive_attempts > remote_no_response_limit:
            remote_name = "No Remote Reading"
        elif remote:
#             r_temp = temp_string("{:.1f}".format(round(sensor.c_to_f(remote["temp"]),1)))
#             r_pres = pres_string("{:.2f}".format(round(sensor.mlb_to_ihg(remote["pres"]),2)))
            r_temp = "{:.1f}".format(round(sensor.c_to_f(remote["temp"]),1))
            remote_name = remote["name"]
        if display:
            if r_temp_save != r_temp:
                display_temp(display,r_temp,remote_row,remote_name)
                r_temp_save = r_temp
            if l_temp_save != l_temp:
                display_temp(display,l_temp,local_row,local_name)
                l_temp_save = l_temp

        else:
            Pin(2).on()
            time.sleep(5)
            Pin(2).off()

            
        if sleep_seconds > 0:
            break # exit to deepsleep
        
        
    deepsleep(sleep_seconds * 1000) # time is millis


def temp_string(value):
    return "Temp: {}".format(value)
            
            
def pres_string(value):
    return "Press: {}".format(value)


def valid_reading(readings):
    try:
        if readings and 'name' in readings and 'temp' in readings and 'pres' in readings:
            return True
    except:
        print("Bad Reading: ",readings)
        pass
    
    return False

class Settings:
    pass

def get_display():
    spi,ss = get_spi('ttgo')
    settings = Settings()
    settings.spi = spi
    settings.debug = False

    settings.display_dc = 21
    settings.display_cs = 13
    settings.display_rst = 23
        
    display = Display(settings)
    display.clear()
#     display._load_fonts() # load the default font
    
    display.centered_text("Starting up...",y=50,width=display.MAX_Y)
    
    return display


def display_temp(display,temp,row,name):
    
    # clear the row
    btn = Button(display.settings,
         name = "label_btn",
         x=0,
         y=row,
         w=int(display.MAX_Y),
         h=ROW_HEIGHT,
         offsets=None,
         label = " ",
         font = None,
         font_color = display.WHITE,
         background = display.BLACK,
         landscape=True,
         )

    btn.show()
    # display the label
    btn.label = name
    btn.w=int(display.MAX_Y/2)
#     print(btn.label,btn.x,btn.y,btn.w,)
    btn.show()
    
    # send each digit to the display one at a time in reverse order
    y=0
    for i in  [x for x in range(len(temp)-1,-1,-1)]:
        glif = get_glif(temp[i])
        display.draw_image("/lib/display/images/{}".format(glif["name"]), x=int(row+(ROW_HEIGHT-glif["h"])/2), y=y, w=glif["h"], h=glif["w"])
        y += glif["w"]
    
def get_glif(s):
    h=80
    w=48
    if not isinstance(s,str) or len(s) != 1 or s[0] not in ["0","1","2","3","4","5","6","7","8","9",".","-",]:
        s="?"
    if s == "1":
        w=38
    elif s ==".":
        w=24
        s = "dot"
    elif s == "-":
        w=38
        s="dash"
    elif s == "?":
        s = "huh"
        
    return {"name":"digit_{}.raw".format(s),"w":w,"h":h,}
            
