"""
    weather_station.py
    
    A device to display the tempurature from two I2C BME units.
    Both units are connected to the same bus but since the device
    address is not changable, I use 2 transistors connected to the
    data line to swap out which device is actually communiting at
    a given time.
    
    
"""

from machine import Pin, SPI, PWM, ADC, RTC
import time as time

HAS_NETWORK = False
try:
    from wifi_connect import Wifi_Connect
    import ntptime
    HAS_NETWORK = True
except:
    pass

from bmx import BMX
from display.display import Display, Button

ROW_HEIGHT = 120 # height of each row in display
CALIBRATION_MODE = True # Display the un-adjusted temp for reference

class Weather_Sensor:
    """Remote tempurature and pressure sensor

    Using BMP sensor to get reading
    """
    
    pass



def start_sensor(**kwargs):
    # set up the pins to switch data sources
    indoor_adjust = kwargs.get("indoor_adjust",0) # temperature correction in C
    outdoor_adjust = kwargs.get("outdoor_adjust",0) # temperature correction in C
    
    # set up to control the screen brightness
    # Set up the light sensor
    daylight = ADC(Pin(27))
    brightness = 65535
    MAX_ADC = 65535

    led = PWM(Pin(8))
    led.duty_u16(MAX_ADC)
    led.freq(5000)
        
    display = get_display()
    
    if HAS_NETWORK:
        # connect to wifi and get the time
        display.centered_text("Waiting for connection",y=50,width=display.MAX_Y)
        wifi_connected = False
        wlan = Wifi_Connect()
        wlan.connect()
        if wlan.status() == 3: # connected and IP obtained
            wifi_connected = True
            print("Connected to",wlan.access_point)
        else:
            print("No Wifi Connection")

    #     has_time = False
    #     try:
    #         ntptime.settime()
    #         has_time = True
    #     except Exception as e:
    #         print("unable to connect to time server:",str(e))
    #         display.centered_text("Time Server Failed",y=75,width=display.MAX_Y)
    #         time.sleep(3)

        dt = DisplayTime()
        if dt.has_time:
            mes = "Got time: " + dt.time_string()
            print(mes)
            display.centered_text(mes,y=75,width=display.MAX_Y)
        else:
            mes = "Don't have time"
            print(mes)
            display.centered_text(mes,y=75,width=display.MAX_Y)

    time.sleep(2)
    display.clear()

    # create 2 sensor instances
    sensors = [] #make a list
    
    try:
        sensors.append(BMX(
                        bus_id=1,
                        scl_pin=19,
                        sda_pin=18,
                        name = "Outdoor",
                        temp_adjust=kwargs.get("outdoor_adjust",0),
                        )
                    )
    except Exception as e:
        mes = "Outdoor sensor Failed"
        print(mes,str(e))
        display.centered_text(mes,y=25,width=display.MAX_Y)
        
    try:
        sensors.append(BMX(
                        bus_id=0,
                        scl_pin=1,
                        sda_pin=0,
                        name = "Indoor",
                        temp_adjust=kwargs.get("indoor_adjust",0)
                        )
                    )
    except Exception as e:
        mes = "Indoor sensor Failed"
        print(mes,str(e))
        display.centered_text(mes,y=50,width=display.MAX_Y)
        
    if len(sensors) < 1:
        time.sleep(5)
        display.clear()
        
    while True:
        display_row = ROW_HEIGHT * -1
        for sensor in sensors:
            display_row += ROW_HEIGHT
            try:
                if CALIBRATION_MODE:
                    print(sensor.name,":",sensor.temperature,end=" ")
                    print("Corrected:",sensor.adjusted_temperature)
                if sensor.temp_changed():
                    display_temp(display,sensor,display_row)

            except Exception as e:
                print("Sensor Error for {}: ".format(sensor.name),str(e))
                display_temp(display,"???",display_row)
                
        # set the display brightness
        # daylight reading gets greater as it gets darker
        brightness = int(daylight.read_u16())
        if brightness > MAX_ADC / 2:
            brightness = 20000
        else:
            brightness = MAX_ADC
            
        led.duty_u16(brightness)

        time.sleep(30)
        

class Settings:
    pass

def get_display():
    settings = Settings()
    settings.spi = SPI(0,
        sck=Pin(2),
        miso=Pin(4),
        mosi=Pin(3),
                )

    settings.debug = False

    settings.display_dc = 6
    settings.display_cs = 5
    settings.display_rst = 7
        
    display = Display(settings)
    display.clear()
    
    display.centered_text("Starting up...",y=25,width=display.MAX_Y)
    
    return display


# def display_temp(display,temp,row,name):
def display_temp(display,sensor,row):
    # display the temperature
    
    unadjusted_temp = ""
    temp = "--"
    name = "Unknown"
    
    if not isinstance(sensor,str):
        try:
            temp = "{:.1f}".format(sensor.c_to_f(sensor.adjusted_temperature)) #Truncate to 1 decimal place
            name = sensor.name
            if CALIBRATION_MODE:
                unadjusted_temp = " (Raw: {:.1f}) ".format(sensor.c_to_f(sensor.saved_temp))
        except:
            temp = "--?"
    
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
    display.draw_text(row+8,
                      display.MAX_Y - 6,
                      name + unadjusted_temp,
                      display.body_font,
                      display.WHITE,
                      background=0,
                      landscape=True,
                      spacing=1,
                      )
    
    # send each digit to the display one at a time in reverse order
    y=10 # set some right margin
    
#     # for testing
#     temp = "-9999.0"
#     print("row: ",row)
    
#     for i in  [x for x in range(len(temp)-1,-1,-1)]:
    for i in range(len(temp)-1,-1,-1):
        glif = get_glif(temp[i])
        display.draw_image("/lib/display/images/{}".format(glif["name"]), x=int(row+(int(display.MAX_X/2)-glif["h"]))-2, y=y, w=glif["h"], h=glif["w"])
        y += glif["w"]
    
def get_glif(s):
    # most images are this size:
    h=80
    w=48
    if not isinstance(s,str) or len(s) != 1 or s[0] not in ["0","1","2","3","4","5","6","7","8","9",".","-",":",]:
        s="?"
    
    if s == "1":
        w=38
    elif s ==".":
        w=24
        s = "dot"
    elif s == "-":
        w=38
        s="dash"
    elif s == ":":
        w=24
        s="colon"
    elif s == "?":
        s = "huh"
        
    return {"name":"digit_{}.raw".format(s),"w":w,"h":h,}
            
           
class DisplayTime:
    
    def __init__(self,format=12,offset_seconds=-28800,has_time=False):
        self.format = format #12 or 24 hour display
        self.offset_seconds = offset_seconds # seconds before or after UTC
        # -12880 is 8 hours before UTC
        self.has_time = has_time #Was the RTC updated from the time server
        
        #try to access the ntp service if needed
        if not self.has_time:
            try:
                ntptime.settime() # always UTC
                print("ntptime:",time.localtime())
                self.has_time = True
                self.set_RTC(self.offset_seconds)
            except Exception as e:
                print("unable to connect to time server:",str(e))

        
    def set_RTC(self,diff_seconds=0):
        """diff_secconds is the number of seconds to add or subtract
            from the current RTC datetime
        """
        t = time.time() + diff_seconds # returns an int
        t = time.localtime(t) # returns a tuple eg: (Y,M,D,H,m,s,weekday,yearday)

        rtc = RTC()
        print("RTC time:",rtc.datetime())
        #set the RTC date time
        rtc.datetime((t[0],t[1],t[2],None,t[3],t[4],t[5],None))
        print("Time set to:",time.localtime())
    
    def time_string(self,format=None):
        if not self.has_time:
            return "--:--"
        if not format:
            format = self.format
        # return the time as text
        t = time.localtime() # returns a tuple
        hrs = t[3]
        if format == 12 and hrs > 12:
            hrs -= 12
        if format == 12 and hrs == 0:
            hrs = 12
        
        hrs = str(hrs)
        
        if format == 24:
            hrs = ("00" + hrs)[-2:]
            
        return hrs + ":" + ("00" + str(t[4]))[-2:]
