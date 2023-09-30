"""
    Main script for Weather Station
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""


from weather_station.weather_station import Weather_Station
from instance.settings import settings

settings.debug = True
# settings.testing = True #Use the testing host
# OTA update settings for testing
# settings.fetch_only = True
# settings.defer_update = True


Weather_Station().start()
