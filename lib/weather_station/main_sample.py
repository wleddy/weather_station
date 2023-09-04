"""
    Main script for Weather Station 2
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""


from instance.settings import settings
settings.debug = True

from weather_station.weather_station import Weather_Station

Weather_Station().start()

