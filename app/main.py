"""
    Main script for Weather Station
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""

from weather_station.weather_station import Weather_Station
from settings.settings import settings, log


settings.debug = False
settings.testing = False #Use the testing host
# OTA update settings for testing
settings.fetch_only = False
# override the host address
# settings._host = 'http://192.168.0.100:5000'

log.setLevel(log.INFO)
log.info("-------------------- Starting up ----------------------")

Weather_Station().start()






