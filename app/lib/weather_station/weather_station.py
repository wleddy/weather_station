"""
    weather_station.py
    
    A device to display the tempurature from two I2C BME units.
    Both units are connected to the same bus but since the device
    address is not changable, I use 2 transistors connected to the
    data line to swap out which device is actually communiting at
    a given time.
    
    
"""

from machine import Pin, SPI, PWM, ADC, RTC
from logging import logging as log
from settings.settings import settings
import time
import json
import urequests
from display.display import Display, Button
from display import glyph_metrics
from ntp_clock import Clock
from wifi_connect import connection
from ota_update.check_for_updates import Check_For_Updates
from weather_station import utils
import gc
gc.enable()

class Weather_Station:
    
    def __init__(self,**kwargs):
            
        # Set up the light sensor
        self.daylight_sensor = ADC(Pin(27))
        self.brightness = kwargs.get('birghtness',65535)
        self.MAX_ADC = 65535
        self.daylight = 65535
        
        # led controls screen brightness
        self.led = PWM(Pin(8))
        self.led.duty_u16(self.MAX_ADC)
        self.led.freq(5000)
        
        self.display = utils.get_display()
        
    def start(self):
        """Run the weather station display loop"""
        
        last_update_check = time.time() - 4000 # force update check on first run
        
        self.display.centered_text(
            "Waiting for connection", y=50, width=self.display.MAX_Y)
            
        clk = Clock()
        clk.set_time()
        if clk.has_time:
            # have wifi connection now...
            mes = "Got time: " + clk.time_string()
            log.info(mes)
        else:
            mes = "Don't have time"
            log.info(mes)
            self.display.clear()
            self.display.centered_text(
                "Connection Failed", y=75, width=self.display.MAX_Y
                )
            time.sleep(2)
            
            
        self.display.clear()
        self.display.centered_text(mes,y=50,width=self.display.MAX_Y)
            
        time.sleep(2)
        self.display.clear()

        prev_style = None
    
        sensors = utils.get_sensors() 

        while True:
            
            glyphs = glyph_metrics.Metrics_78()
            if not clk.has_time and clk.last_sync_seconds < time.time() - 60:
                # if we just tryied to get the time and failed, don't try for a while
                clk.set_time()
                   
            if clk.has_time:
                style = "time"
            else:
                style = "no time"
                
            force_refresh = False
            
            # set the display brightness
            # daylight reading gets greater as it gets darker
            self.daylight = int(self.daylight_sensor.read_u16())
            self.brightness = self.MAX_ADC - int(self.daylight * .25)
            if self.brightness < 20000:
                self.brightness = 20000

            self.led.duty_u16(self.brightness)
            
            if style != prev_style:
                prev_style = style
                force_refresh = True
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
                
            #only interested in the last two elements for temperatures
            display_rows = self.display_coords[-2:] 
            
            row = 0
            changed_sensors = []
            
            for sensor in sensors:
                if sensor.temp_changed() or force_refresh:
                    try:
                        changed_sensors.append(sensor)
                        utils.hinlow(sensor.name,sensor.adjusted_temperature)
                        self.display_temp(sensor,display_rows[row],glyphs)
                    except Exception as e:
                        log.exception(e,f"Sensor Error for {sensor.name}")
                        self.display_temp(sensor,display_rows[row],glyphs)
                        
                log.info(f'Reading- {sensor.name}: raw; {sensor.c_to_f(sensor.temperature)}, adjusted; {sensor.adjusted_temperature}')
                row +=1
                       
            # Export changed readings
            for sensor in changed_sensors:
                try:
                    utils.export_reading(sensor)
                except Exception as e:
                    log.info(f'Sensor {sensor.name} export failed')
                
            if clk.last_sync_seconds < (time.time() - (3600 * 24)):
                # if it's been longer than 24 hours since last sync update the clock
                clk.set_time()

            if last_update_check < time.time() - 3600: # Only check once an hour
                last_update_check = time.time()
                try:
                    Check_For_Updates().run()
                except Exception as e:
                    log.exception(e,f"Error during update attempt")
                
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
            except Exception as e:
                log.exception(e,f'Error adjusting temperature')
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
        
        # for testing
#         temp = "199.0"
        
        
        # Finnally, display the temperture
        self.draw_glyphs(glyphs,row[0],row[1],temp)
        
        # high and low temps
        # show the low temp if present
        hiorlow = utils.hinlow()
        try:
            temp = int(float(temp))
        except:
            # this can happen if temp is NaN
            temp = None
            
        if temp is not None:
            if temp >= 100 or hiorlow[sensor.name]['high'] >= 100:
                # use smaller type
                glyphs = glyph_metrics.Metrics_27()
            else:
                glyphs = glyph_metrics.Metrics_37()
                
            old_path = glyphs.path
            glyphs.path = old_path + 'blue/'
            text = str(hiorlow[sensor.name]['low'])
            x = row[0]+30        
            y = self.display.MAX_Y - 6 - glyphs.string_width(text)
            self.draw_glyphs(glyphs,x,y,text)
            glyphs.path = old_path + 'red/'
            text = str(hiorlow[sensor.name]['high'])
            y = y - int(glyphs.WIDTH/2) - glyphs.string_width(text)
            self.draw_glyphs(glyphs,x,y,text)

        
    def draw_glyphs(self,glyphs,x,y,value):
        # send each digit to the display one at a time in reverse order

        for i in range(len(value)-1,-1,-1):
            glyph = glyphs.get(value[i])
            self.display.draw_image(glyph['path'], x=x, y=y, w=glyph["h"], h=glyph["w"])
            y += glyph["w"]


        
