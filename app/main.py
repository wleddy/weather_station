"""
    Main script for Weather Station
    
    I abandoned my original idea of using the LoRa radios
    to communicate between the indoor and outdoor units.
    
    Now just use an extension wire bus to put the exterior
    sensor out the window.

"""


def main():
    from logging import logging as log
    from weather_station.weather_station import Weather_Station
    from settings.settings import settings
    import machine
    
    log.setLevel(log.INFO)
    
    # OTA update settings for testing
    settings.fetch_only = False
    # override the host address from instance/instance.py
    # settings.host = 'http://wide-ride.local:5000'

    log.info("-------------------- Starting up ----------------------")

    try:
        Weather_Station().start()
    except Exception as e:
        log.exception(e,'Exception in main.py')
        machine.reset()


if __name__ == '__main__':
    main()




