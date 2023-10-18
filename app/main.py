"""
    Main script for Weather Station
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""

# Create the instance directory if not present and insert device details
from os_path import make_path, exists
filename = '/instance/instance.py'

device_info = """
device_id = 1

sensors = [
    {'name':'Outdoor', 'sensor_id':2, 'scale':'f', 'device_id': device_id,},
    {'name':'Indoor', 'sensor_id':1, 'scale':'f', 'device_id': device_id,},
    ]

host = 'http://tc.williesworkshop.net'

    """
if not exists(filename) and make_path(filename):
    with open(filename,'w') as f:
        f.write(device_info)
        

def main():
    from weather_station.weather_station import Weather_Station
    from settings.settings import settings, log


    settings.debug = False
    settings.testing = True #Use the testing host
    # OTA update settings for testing
    settings.fetch_only = False
    # override the host address
    # settings._host = 'http://192.168.0.100:5000'

    log.setLevel(log.INFO)
    log.info("-------------------- Starting up ----------------------")


    Weather_Station().start()

main()




