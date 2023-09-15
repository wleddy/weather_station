"""
    Main script for Weather Station
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""


from weather_station.weather_station import Weather_Station
from senko import check_for_updates

check_for_updates.run()

Weather_Station().start()
