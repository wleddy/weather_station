"""
    weather_station.py
    
    A device to display the tempurature from two I2C BME units.
    Both units are connected to the same bus but since the device
    address is not changable, I use 2 transistors connected to the
    data line to swap out which device is actually communiting at
    a given time.
    
    
"""

from machine import Pin, SPI, PWM, ADC
from instance.settings import settings
import time as time

from bmx import BMX
from display.display import Display, Button
import glyph_metrics
from ntp_clock import Clock


class Weather_Station:
    
    def __init__(self,**kwargs):
        self.indoor_adjust = kwargs.get("indoor_adjust",0) # temperature correction in C
        self.outdoor_adjust = kwargs.get("outdoor_adjust",0) # temperature correction in C
        if not settings.debug:
            settings.debug = kwargs.get("debug",False)
            
        # Set up the light sensor
        self.daylight_sensor = ADC(Pin(27))
        self.brightness = kwargs.get('birghtness',65535)
        self.MAX_ADC = 65535
        self.daylight = 65535
        
        # led controls screen brightness
        self.led = PWM(Pin(8))
        self.led.duty_u16(self.MAX_ADC)
        self.led.freq(5000)
        
        self.display = get_display()
        
    def start(self):
    
        self.display.centered_text("Waiting for connection",y=50,width=self.display.MAX_Y)

        clk = Clock()
        clk.set_time()
        if clk.has_time:
            mes = "Got time: " + clk.time_string()
            print(mes)
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
                            bus_id = settings.bmx_0_bus_id,
                            scl_pin = settings.bmx_0_scl_pin,
                            sda_pin = settings.bmx_0_sda_pin,
                            name = settings.bmx_0_name,
                            temp_calibration_list = settings.bmx_0_cal_data,
                            temp_scale = settings.bmx_0_temp_scale,
                            )
                        )
        except Exception as e:
            print(e)
            mes = "Outdoor sensor Failed"
            print(mes,str(e))
            self.display.centered_text(mes,y=25,width=self.display.MAX_Y)
        
        try:
            sensors.append(BMX(
                            bus_id = settings.bmx_1_bus_id,
                            scl_pin = settings.bmx_1_scl_pin,
                            sda_pin = settings.bmx_1_sda_pin,
                            name = settings.bmx_1_name,
                            temp_calibration_list = settings.bmx_1_cal_data,
                            temp_scale = settings.bmx_1_temp_scale,
                            )
                        )
        except Exception as e:
            print(e)
            mes = "Indoor sensor Failed"
            print(mes,str(e))
            self.display.centered_text(mes,y=50,width=self.display.MAX_Y)
        
        if len(sensors) < 2:
            time.sleep(5)
            self.display.clear()
    
        prev_style = None
        glyphs = glyph_metrics.Metrics_78()
    
        while True:
            if not clk.has_time and clk.last_sync_seconds < time.time() - 60:
                # if we just tryied to get the time and failed, don't try for a while
                clk.set_time()
                   
            if clk.has_time:
                style = "time"
            else:
                style = "no time"
        
            if style != prev_style:
                prev_style = style
                if clk.has_time:
                    # divide screen into 3 regions
                    # display_coords is a list of tuples that describe the native
                    # coords of the regions to be used for each display row
                    # as (x,y,h,w) 
                    pad = (2,6) # (x,y)
                    self.display_coords = [
                        (0,pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        (pad[0]+int(self.display.MAX_X*.333),pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        (pad[0]+int(self.display.MAX_X*.666),pad[1],glyphs.HEIGHT,self.display.MAX_Y),
                        ]
                else:
                    # divide screen into 2 regions
                    pad = (15,6) # (x,y)
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

            if clk.has_time:
                t = " "+clk.time_string()+" "
                l = glyphs.string_width(t)
                # Display the time (native coords)
                self.draw_glyphs(glyphs,self.display_coords[0][0],self.display_coords[0][1]-pad[1]+int((self.display.MAX_Y-l)/2),t)
                
            display_rows = self.display_coords[-2:] #only interested in the last two elements for temperatures
            row = 0
            for sensor in sensors:
                try:
                    if sensor.temp_changed():
                        self.display_temp(sensor,display_rows[row],glyphs)
                        if settings.debug:
                            print(sensor.name,":",sensor.saved_temp)
                            settings.debug = False #turn off to avoid double debug messages
                            print(sensor.name,"Corrected:",sensor.adjusted_temperature)
                            settings.debug = True

                except Exception as e:
                    print("Sensor Error for {}: ".format(sensor.name),str(e))
                    self.display_temp(sensor,display_rows[row],glyphs)
                    
                row +=1
                       
            # set the display brightness
            # daylight reading gets greater as it gets darker
            self.daylight = int(self.daylight_sensor.read_u16())
            if settings.debug:
                self.display.draw_text(
                      0,
                      self.display.MAX_Y,
                      "Dl: " + str(self.daylight),
                      self.display.body_font,
                      self.display.WHITE,
                      background=0,
                      landscape=True,
                      spacing=1,
                      )
            self.brightness = self.MAX_ADC - int(self.daylight * .75)
            if self.brightness < 20000:
                self.brightness = 20000

            self.led.duty_u16(self.brightness)
            if settings.debug:
                self.display.draw_text(
                      25,
                      self.display.MAX_Y,
                      "Br: " + str(self.brightness),
                      self.display.body_font,
                      self.display.WHITE,
                      background=0,
                      landscape=True,
                      spacing=1,
                      )
            
            if clk.last_sync_seconds < (time.time() - (3600 * 24)):
                # if it's been longer than 24 hours since last sync update the clock
                clk.set_time()
                
            # Sync the display time to the top of the minute
            # then sleep for 1 minute
            time.sleep(60 - time.localtime()[5])
              

    def display_temp(self,sensor,row,glyphs):
        # display the temperature
        # row is now a tuple as (x,y)
        
        raw_temp = ""
        calibration_factor = ""
        temp = "--"
        name = "Unknown"

        if not isinstance(sensor,str):
            try:
                temp = "{:.1f}".format(sensor.adjusted_temperature) #Truncate to 1 decimal place
                name = sensor.name
                if settings.debug:
                    raw_temp = "Raw: {:.1f}".format(sensor.saved_temp)
                    calibration_factor = "Cal: {:.2f}".format(sensor.calibration_factor)
            except Exception as e:
                print(str(e))
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
        self.display.draw_text(
                      row[0],
                      self.display.MAX_Y - 6,
                      name,
                      self.display.body_font,
                      self.display.WHITE,
                      background=0,
                      landscape=True,
                      spacing=1,
                      )
        # show the uncorrected value if present
        self.display.draw_text(
                      row[0]+24,
                      self.display.MAX_Y - 6,
                      raw_temp,
                      self.display.body_font,
                      self.display.WHITE,
                      background=0,
                      landscape=True,
                      spacing=1,
                      )
        # show the calibration factor if present
        self.display.draw_text(
                      row[0]+48,
                      self.display.MAX_Y - 6,
                      calibration_factor,
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


def get_display():
    display = Display(settings)
    display.debug = False
    display.clear()
    
    display.centered_text("Starting up...",y=25,width=display.MAX_Y)
    
    return display

           
        
        
