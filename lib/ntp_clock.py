"""Clock class to connect to the NTP server via wifi and set
the Real Time Clock.
    
    A wifi connection will be attempted if one is not already available when
    setting the time. If there is no connection prior to the call the connection
    will be closed and the wifi will be de-activated otherwise the conncetion will
    be used and left as is.
"""

from machine import RTC
from instance.settings import settings
import time as time


class Clock:
    
    def __init__(self,format=12,offset_seconds=-28800):
        self.format = format #12 or 24 hour display
        self.offset_seconds = offset_seconds # seconds before or after UTC
        # -12880 is 8 hours before UTC
        
        self.has_time = False
        self.UTC_time = None
        self.last_sync_seconds = time.time()
        self.network_active = False

    
    def _connect(self):
        if not getattr(settings,"wlan",False):
            try:
                from wifi_connect import Wifi_Connect
                settings.wlan = Wifi_Connect()

            except Exception as e:
                if settings.debug:
                    print("settings.wlan not created:",str(e))
                    
                return
                    
        # a Wifi_Connect instance is avaialble
        try:
            # preserve the current active status
            self.network_active = settings.wlan.active()

            if not settings.wlan.isconnected():
                settings.wlan.connect()
                if not settings.wlan.isconnected():
                    return
        except Exception as e:
            if settings.debug:
                print("Could not activate connection:",str(e))
                    

    def set_time(self):
        """Try to access the NTP system to set the real time clock"""
        
        self.has_time = False
        # update to the current time just to show we tried...
        self.last_sync_seconds = time.time() 
   
        self._connect()
        
        try:
            import ntptime
            ntptime.settime() # always UTC
            self.UTC_time = time.gmtime()
            print("ntptime:",time.localtime())
            self.has_time = True
            self.set_RTC()
            self.last_sync_seconds = time.time()
        except Exception as e:
            print("unable to connect to time server:",str(e))
        
        # disconnect from the wlan if the connection was opened here
        if not self.network_active:
            try:
                settings.wlan.disconnect()
                settings.wlan.active(False)
            except Exception as e:
                if settings.debug:
                    print("Unable to reset network state:",str(e))
            
 
    def set_RTC(self):
        """Set the Real Time Clock for the local time
        """
        
        t = time.time() + self.offset_seconds # returns an int
        t = time.localtime(t) # returns a tuple eg: (Y,M,D,H,m,s,weekday,yearday)

        rtc = RTC()
        print("RTC time:",rtc.datetime())
        #set the RTC date time to adjusted local time
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
        
