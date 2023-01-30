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

WIFI_PRESENT = False #Does the UMC have Wifi?

try:
    from wifi_connect import Wifi_Connect
    import ntptime
    WIFI_PRESENT = True
except:
    pass

from bmx import BMX
from display.display import Display, Button
import glyph_metrics

CALIBRATION_MODE = False # Display the un-adjusted temp for reference

class Weather_Station:
    
    def __init__(self,**kwargs):
        # set up the pins to switch data sources
        self.indoor_adjust = kwargs.get("indoor_adjust",0) # temperature correction in C
        self.outdoor_adjust = kwargs.get("outdoor_adjust",0) # temperature correction in C
    
        # set up to control the screen brightness
        # Set up the light sensor
        self.daylight = ADC(Pin(27))
        self.brightness = kwargs.get('birghtness',65535)
        self.MAX_ADC = 65535

        self.led = PWM(Pin(8))
        self.led.duty_u16(self.MAX_ADC)
        self.led.freq(5000)

        self.display = get_display()
        
        
        
    def start(self):
    
        if WIFI_PRESENT:
            # connect to wifi and get the time
            self.display.centered_text("Waiting for connection",y=50,width=self.display.MAX_Y)
            wifi_connected = False
            wlan = Wifi_Connect()
            wlan.connect()
            if wlan.status() == 3: # connected and IP obtained
                wifi_connected = True
                print("Connected to",wlan.access_point)
            else:
                print("No Wifi Connection")

        dt = DisplayTime()
        if dt.has_time:
            mes = "Got time: " + dt.time_string()
            print(mes)
            self.display.centered_text(mes,y=75,width=self.display.MAX_Y)
        else:
            mes = "Don't have time"
            print(mes)
            self.display.centered_text(mes,y=75,width=self.display.MAX_Y)

        time.sleep(2)
        self.display.clear()

        # create 2 sensor instances
        sensors = [] #make a list
    
        try:
            sensors.append(BMX(
                            bus_id=1,
                            scl_pin=19,
                            sda_pin=18,
                            name = "Outdoor",
                            temp_adjust=self.outdoor_adjust,
                            )
                        )
        except Exception as e:
            mes = "Outdoor sensor Failed"
            print(mes,str(e))
            self.display.centered_text(mes,y=25,width=self.display.MAX_Y)
        
        try:
            sensors.append(BMX(
                            bus_id=0,
                            scl_pin=1,
                            sda_pin=0,
                            name = "Indoor",
                            temp_adjust=self.indoor_adjust,
                            )
                        )
        except Exception as e:
            mes = "Indoor sensor Failed"
            print(mes,str(e))
            self.display.centered_text(mes,y=50,width=self.display.MAX_Y)
        
        if len(sensors) < 2:
            time.sleep(5)
            self.display.clear()
    
        prev_style = None
    
        while True:
            if not dt.has_time:
                dt.set_time()
            
            if dt.has_time:
                glyphs = glyph_metrics.Metrics_78()
                style = "time"
            else:
                glyphs = glyph_metrics.Metrics_78()
                style = "no time"
        
            if style != prev_style:
                prev_style = style
                pad = (2,6) # (x,y)
                if dt.has_time:
                    # divide screen into 3 regions
                    # display_coords is a list of tuples that describe the native
                    # coords of the regions to be used for each display row
                    # as (x,y,h,w) 
                    self.display_coords = [
                        (0,pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        (pad[0]+int(self.display.MAX_X*.333),pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        (pad[0]+int(self.display.MAX_X*.666),pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        ]
                else:
                    # divide screen into 2 regions
                    pad = (8,6) # (x,y)
                    self.display_coords = [
                        (pad[0],pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        (pad[0]+int(self.display.MAX_X*.5),pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        ]
                    
                # draw some lines
                self.display.clear()
                # Draw the lines after the fact
                for row in range(1,len(self.display_coords)):
                    # draw_line(x1, y1, x2, y2, color) in native coords
                    self.display.draw_line(self.display_coords[row][0]-pad[0],
                                           self.display_coords[row][1]-pad[1],
                                           self.display_coords[row][0]-pad[0],
                                           self.display_coords[row][3],
                                           self.display.RED)

            if dt.has_time:
                t = " "+dt.time_string()+" "
                l = glyphs.string_width(t)
                # Display the time (native coords)
                self.draw_glyphs(glyphs,self.display_coords[0][0],self.display_coords[0][1]-pad[1]+int((self.display.MAX_Y-l)/2),t)
                
            display_rows = self.display_coords[-2:] #only interested in the last two elements for temperatures
            row = 0
            for sensor in sensors:
                try:
                    if CALIBRATION_MODE:
                        print(sensor.name,":",sensor.temperature,end=" ")
                        print("Corrected:",sensor.adjusted_temperature)
                    if sensor.temp_changed():
                        self.display_temp(sensor,display_rows[row],glyphs)

                except Exception as e:
                    print("Sensor Error for {}: ".format(sensor.name),str(e))
                    self.display_temp(sensor,display_rows[row],glyphs)
                    
                row +=1
                       
            # set the display brightness
            # daylight reading gets greater as it gets darker
            self.brightness = int(self.daylight.read_u16())
            if self.brightness > self.MAX_ADC / 2:
                self.brightness = 20000
            else:
                self.brightness = self.MAX_ADC
            
            self.led.duty_u16(self.brightness)
            
            time.sleep(30)
        

    def display_temp(self,sensor,row,glyphs):
        # display the temperature
        # row is now a tuple as (x,y)
        
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
        btn = Button(self.display.settings,
             name = "label_btn",
             x=row[1],
             y=row[0],
             h=row[2],
             w=row[3],
             offsets=None,
             label = " ",
             font = None,
             font_color = self.display.WHITE,
             background = self.display.BLACK,
             landscape=True,
             )

        btn.show()

        # Label the value
        # add a bit to row to create a little top padding
        self.display.draw_text(
                      row[0],
                      self.display.MAX_Y - 6,
                      name + unadjusted_temp,
                      self.display.body_font,
                      self.display.WHITE,
                      background=0,
                      landscape=True,
                      spacing=1,
                      )

        # for testing
#         temp = "199.0"

        # Finnally, display the temperture
        self.draw_glyphs(glyphs,row[0],row[1],temp)

    def draw_glyphs(self,glyphs,x,y,value):
        # send each digit to the display one at a time in reverse order

        for i in range(len(value)-1,-1,-1):
            glyph = glyphs.get(value[i])
            self.display.draw_image(glyph['path'], x=x, y=y, w=glyph["h"], h=glyph["w"])
            y += glyph["w"]


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

           
class DisplayTime:
    
    def __init__(self,format=12,offset_seconds=-28800):
        self.format = format #12 or 24 hour display
        self.offset_seconds = offset_seconds # seconds before or after UTC
        # -12880 is 8 hours before UTC
        self.has_time = False
        
        #try to access the ntp service if needed
        self.set_time()

    def set_time(self):
        """Try to access the NTP system to set the real time clock"""
        try:
            ntptime.settime() # always UTC
            print("ntptime:",time.localtime())
            self.has_time = True
            self.set_RTC()
        except Exception as e:
            self.has_time = False
            print("unable to connect to time server:",str(e))

 
    def set_RTC(self):
        """Set the Real Time Clock for the local time
        """
        
        t = time.time() + self.offset_seconds # returns an int
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
        
        
        
