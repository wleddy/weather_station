"""
    Main script for Weather Station 2
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""

# from weather_station import weather_station
# 
# #adjustments are in degrees C to compensate for errors in device readings
# weather_station.start_sensor()

from instance.settings import settings
settings.debug = True
#settings.WIFI_PRESENT = False

from weather_station.weather_station import Weather_Station

Weather_Station().start()
