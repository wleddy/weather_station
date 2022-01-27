"""
    weather_station.py
    
    A device to display the tempurature from two I2C BME units.
    Both units are connected to the same bus but since the device
    address is not changable, I use 2 transistors connected to the
    data line to swap out which device is actually communiting at
    a given time.
    
    
"""
import json
from machine import Pin
import utime as time

from bmx280_bl import BMX280
from spi_setup.spi_setup import get_spi
from display.display import Display, Button

ROW_HEIGHT = 120 # height of each row in display


class WeatherSensor:
    """Remote tempurature and pressure sensor

    Using BMP sensor to get reading
    """
    
    def __init__(self,scl_pin=15,sda_pin=4,freq=500000):
        self.bmx = BMX280(scl=scl_pin,sda=sda_pin,freq=freq)
                
    
    def read(self):
        """Get a reading"""
        return {'pres':self.bmx.pressure,'temp':self.bmx.temperature}


    def c_to_f(self,temp_c):
        """Convert centigrade to Fahrenheit"""
        
        return (temp_c * 1.8) + 32

    
    def mlb_to_ihg(self,mlb):
        """Convert milibars to inches of mercury"""
        
        return mlb * 0.00029529980164712


def start_sensor(**kwargs):

    # set up the pins to switch data sources
    indoor_data_connect = Pin(17,Pin.OUT)    
    indoor_adjust = kwargs.get("indoor_adjust",0) # temperature correction in C
    
    outdoor_data_connect = Pin(12,Pin.OUT)
    outdoor_adjust = kwargs.get("outdoor_adjust",0) # temperature correction in C
    
    # initiallize the sensor object
    outdoor_data_connect.off()
    indoor_data_connect.on()
    time.sleep(2)
    sensor = WeatherSensor(freq=100000)
    
    display = get_display()
    
    outdoor_row = 0
    indoor_row = outdoor_row + ROW_HEIGHT
    
    indoor_name = "Indoor"
    outdoor_name = "Outdoor"
    indoor_temp_save = None
    outdoor_temp_save = None
    
    while True:
        try:
            outdoor_data_connect.off()
            indoor_data_connect.on()
            time.sleep(2)
            indoor = sensor.read()
            print("Indoor: ",indoor,end=' ')
            indoor_data_connect.off()
            indoor["temp"] += indoor_adjust # apply manual correction
            print("Indoor Corrected:",indoor["temp"])
        except Exception as e:
            print("Indoor Error: ",str(e))
            indoor = None
            
        try:
            indoor_data_connect.off()
            outdoor_data_connect.on()
            time.sleep(2)
            outdoor = sensor.read()
            outdoor_data_connect.off()
            print("Outdoor: ",outdoor,end=' ')
            outdoor["temp"] += outdoor_adjust # apply manual correction
            print("Outdoor Corrected:",outdoor["temp"])
        except Exception as e:
            print("Outdoor Error: ",str(e))
            outdoor = None

        indoor_temp = outdoor_temp = "?"
        
        if indoor:
            indoor_temp = "{:.1f}".format(round(sensor.c_to_f(indoor["temp"]),1))
        if outdoor:
            outdoor_temp = "{:.1f}".format(round(sensor.c_to_f(outdoor["temp"]),1))
        if outdoor_temp_save != outdoor_temp:
            display_temp(display,outdoor_temp,outdoor_row,outdoor_name)
            outdoor_temp_save = outdoor_temp
        if indoor_temp_save != indoor_temp:
            display_temp(display,indoor_temp,indoor_row,indoor_name)
            indoor_temp_save = indoor_temp
                
        time.sleep(20)


def valid_reading(readings):
    try:
        if readings and 'temp' in readings and 'pres' in readings:
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
    # display the temperature
    
    # clear the row
    btn = Button(display.settings,
         name = "label_btn",
         x=0,
         y=row + 2, # down a bit so the dividing line isn't cleared
         w=int(display.MAX_Y),
         h=ROW_HEIGHT - 6, # same as above for bottom padding
         offsets=None,
         label = " ",
         font = None,
         font_color = display.WHITE,
         background = display.BLACK,
         landscape=True,
         )

    btn.show()
    
    # draw a divider line
    # draw_line(x1, y1, x2, y2, color)
    display.draw_line(int(display.MAX_X/2), 0, int(display.MAX_X/2), display.MAX_Y, display.RED)
    
    # add a bit to row to create a little top padding
    display.draw_text(row+8, display.MAX_Y - 6, name, display.body_font, display.WHITE,  background=0,
                  landscape=True, spacing=1)
    
    # send each digit to the display one at a time in reverse order
    y=10 # set some right margin
    
#     # for testing
#     temp = "-9999.0"
#     print("row: ",row)
    
    for i in  [x for x in range(len(temp)-1,-1,-1)]:
        glif = get_glif(temp[i])
        display.draw_image("/lib/display/images/{}".format(glif["name"]), x=int(row+(int(display.MAX_X/2)-glif["h"]))-2, y=y, w=glif["h"], h=glif["w"])
        y += glif["w"]
    
def get_glif(s):
    # most images are this size:
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
            
