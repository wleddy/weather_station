"""
    weather_station.py
    
    A device to display the tempurature from two I2C BME units.
    Both units are connected to the same bus but since the device
    address is not changable, I use 2 transistors connected to the
    data line to swap out which device is actually communiting at
    a given time.
    
    
"""

from machine import Pin, SPI, PWM, ADC
import utime as time

from bmx280_bl import BMX280
from spi_setup.spi_setup import get_spi
from display.display import Display, Button

ROW_HEIGHT = 120 # height of each row in display
CALIBRATION_MODE = True # Display the un-adjusted temp for reference

class WeatherSensor:
    """Remote tempurature and pressure sensor

    Using BMP sensor to get reading
    """
    
    pass

class BMX:
    
    def __init__(self,
                 scl_pin=1,
                 sda_pin=0,
                 freq=100000,
                 bus_id=None,
                 name="Unknown BMX",
                 temp_adjust=0,
                 press_adjust=0,
                 ):
        
        self.bmx = None
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.freq = freq
        self.bus_id = bus_id
        self.name=name
        self.temp_adjust = temp_adjust
        self._saved_temp = 0
        self.press_adjust = press_adjust
        self._saved_press = 0
        
        self.bmx = BMX280(
            bus_id=self.bus_id,
            scl=self.scl_pin,
            sda=self.sda_pin,
            freq=self.freq,
            )

    def read(self):
        """Get a reading"""
        return {'pres':self.bmx.pressure,'temp':self.bmx.temperature}
        
    @property
    def temperature(self):
        return self.bmx.temperature

    @property
    def adjusted_temperature(self):
        return self.saved_temp + self.temp_adjust
    
    @property
    def saved_temp(self):
        return self._saved_temp / 10
    
    def temp_changed(self):
        # test/save the temp as an int to reduce rounding error
        temp = int(self.temperature * 10)
        if temp != self._saved_temp:
            self._saved_temp = temp
            return True
        return False
    
    def c_to_f(self,temp_c):
        """Convert centigrade to Fahrenheit"""
        return (temp_c * 1.8) + 32

    @property
    def pressure(self):
        return self.bmx.pressure
    
    @property
    def adjusted_pressure(self):
        return self.pressure + self.press_adjust
    
    def mlb_to_ihg(self,mlb):
        """Convert milibars to inches of mercury"""
        
        return mlb * 0.00029529980164712


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
        
        sensors.append(BMX(
                        bus_id=0,
                        scl_pin=1,
                        sda_pin=0,
                        name = "Indoor",
                        temp_adjust=kwargs.get("indoor_adjust",0)
                        )
                    )
    except Exception as e:
        display.clear()
        display.centered_text("Failed to connect sensor")
        
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
#     spi,ss = get_spi('ttgo')
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
    
    display.centered_text("Starting up...",y=50,width=display.MAX_Y)
    
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
            
