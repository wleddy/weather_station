"""Run code to check for updates if available and restart
as needed.
"""
from instance.settings import settings
import machine
from senko import senko
from wifi_connect import Wifi_Connect
import time

def run():
    #   url='https://github.com/wleddy/weather_station/tree/master/app/'

 
    settings.wlan = Wifi_Connect()
    settings.wlan.connect()
    
    i = 0
    while not settings.wlan.is_connected():
        i += 1
        time.sleep(1)
        if i >= 10:
            return
        
    OTA = senko.Senko(
        user="wleddy", repo="weather_station",
        files=['main.py','senko/check_for_updates.py','senko/senco.py',]
        )

        
    if OTA.update():
        print("Updated to the latest version! Rebooting...")
        machine.reset()
    else:
        print('No update needed')
