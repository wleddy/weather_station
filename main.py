"""Main script for Weather Station sensor and base station

Comment out one section or the other
"""

from weather_station import weather_station


# # Use the same call for remote and local
# # Set sleep_seconds to 0 for the local, always on display
# # Set the sleep_seconds to something else for the remote, battery powered unit
# # Remote runs one time successfully, then goes into deep sleep
# #    for 'sleep_seconds'
# # After deep sleep, mpu re-runs this script
# t_adjust is a manual adjustment to the centegrade reading from the BME280
weather_station.start_sensor('Back Yard',sleep_seconds=60,t_adjust=-2.862) 
