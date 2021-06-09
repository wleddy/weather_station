"""Main script for Weather Station sensor and base station

Comment out one section or the other
"""

from weather_station import weather_station


# # Remote Sensor
# # Runs one time successfully, then goes into deep sleep
# #    for 'sleep' seconds
# # After deep sleep, mpu re-runs this script
# weather_station.start_sensor('grommet',sleep_seconds=60) 


# # Main Weather Station
# # runs forever...
weather_station.start_receiver()

