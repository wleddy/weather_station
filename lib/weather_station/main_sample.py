"""
    Main script for Weather Station 2
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""

from weather_station.weather_station import Weather_Station

Weather_Station(
    outdoor_adjust=-5.88888888888891,
    indoor_adjust=-2.83333333333333,
    ).start()
