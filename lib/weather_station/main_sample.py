"""
    Main script for Weather Station 2
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""

from weather_station import weather_station


# adjustments are in degrees C to compensate for errors in device readings
# weather_station.start_sensor(sleep_seconds=0,
#                              outdoor_adjust=-1.7222222222222,
#                              indoor_adjust=-2.83333333333333,
#                              ) 
weather_station.start_sensor(sleep_seconds=0,
                             outdoor_adjust=-5.88888888888891,
                             indoor_adjust=-2.83333333333333,
                             ) 

