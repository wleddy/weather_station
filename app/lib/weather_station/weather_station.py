"""
    weather_station.py
    
    A device to display the tempurature from two I2C BME units.
    Both units are connected to the same bus but since the device
    address is not changable, I use 2 transistors connected to the
    data line to swap out which device is actually communiting at
    a given time.
    
    
"""

from machine import Pin, SPI, PWM, ADC, RTC
from settings.settings import settings, log
import time
import json
import urequests
from bmx import BMX
from display.display import Display, Button
from display import glyph_metrics
from ntp_clock import Clock
from wifi_connect import connection
from ota_update.check_for_updates import Check_For_Updates

import gc
gc.enable()

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
        """Run the weather station display loop"""
        
        last_update_check = time.time()
        
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
            
        if connection.is_connected():
            # check for updates
            self.display.centered_text(
                "Checking for updates...", y=75, width=self.display.MAX_Y)
            try:
                Check_For_Updates(display=None,fetch_only=False).run()
            except Exception as e:
                log.exception(e,f'Initial update attempt failed: {str(e)}')
                
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
                            sensor_id = settings.bmx_0_sensor_id,
                            temp_calibration_list = settings.bmx_0_cal_data,
                            temp_scale = settings.bmx_0_temp_scale,
                            )
                        )
        except Exception as e:
            mes = f"Outdoor sensor Failed"
            log.exception(e,f'{mes}, {str(e)}')
            self.display.centered_text(mes,y=25,width=self.display.MAX_Y)
        
        try:
            sensors.append(BMX(
                            bus_id = settings.bmx_1_bus_id,
                            scl_pin = settings.bmx_1_scl_pin,
                            sda_pin = settings.bmx_1_sda_pin,
                            name = settings.bmx_1_name,
                            sensor_id = settings.bmx_1_sensor_id,
                            temp_calibration_list = settings.bmx_1_cal_data,
                            temp_scale = settings.bmx_1_temp_scale,
                            )
                        )
        except Exception as e:
            mes = f"Indoor sensor Failed"
            log.exception(e,f'{mes}, {str(e)}')
            self.display.centered_text(mes,y=50,width=self.display.MAX_Y)
        
        if len(sensors) < 2:
            time.sleep(5)
            self.display.clear()
    
        prev_style = None
    
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
                
            display_rows = self.display_coords[-2:] #only interested in the last two elements for temperatures
            row = 0
            changed_sensors = []
            # update the highs and lows
            # if any change, display all
            for sensor in sensors:
                if sensor.temp_changed() or force_refresh:
                    changed_sensors.append(sensor)
                hinlow(sensor.name,sensor.adjusted_temperature)
                    
            for sensor in sensors:
                try:
                    if changed_sensors:
                        self.display_temp(sensor,display_rows[row],glyphs)
                        log.info(f"{sensor.name}: {sensor.saved_temp}")
                        log.debug(f"{sensor.name}, Corrected: {sensor.adjusted_temperature}")
                    else:
                        log.debug(f"No Temp change for sensor {sensor.name}")


                except Exception as e:
                    log.exception(e,f"Sensor Error for {sensor.name}")
                    self.display_temp(sensor,display_rows[row],glyphs)
                    
                row +=1
                       
            # set the display brightness
            # daylight reading gets greater as it gets darker
            self.daylight = int(self.daylight_sensor.read_u16())
            self.brightness = self.MAX_ADC - int(self.daylight * .25)
            if self.brightness < 20000:
                self.brightness = 20000

            self.led.duty_u16(self.brightness)
            
            # Export changed readings
            for sensor in changed_sensors:
                try:
                    export_reading(sensor)
                except Exception as e:
                    log.info(f'Sensor {sensor.name} export failed, {str(e)}')
                
            if clk.last_sync_seconds < (time.time() - (3600 * 24)):
                # if it's been longer than 24 hours since last sync update the clock
                clk.set_time()

            if last_update_check < time.time() - 3600: # Only check once an hour
                last_update_check = time.time()
                try:
                    # check for updates
                    Check_For_Updates(display=None, fetch_only=False).run()
                except Exception as e:
                    log.exception(e,f"Error during update attempt: {str(e)}")
                
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
                log.error(f'Error adjusting temperature: {str(e)}')
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
        hiorlow = hinlow()
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


def get_display():
    display = Display(settings)
    display.debug = False
    display.clear()
    
    display.centered_text("Starting up...",y=25,width=display.MAX_Y)
    
    return display

           
def export_reading(sensor):
    #Send the current temp to the temp_center app
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
            del r
            gc.collect()
            
        except Exception as e:
            log.exception(e,f"Export Reading Failed for {sensor.name}: {str(e)}")
            gc.enable()
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

        
