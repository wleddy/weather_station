"""Keep a list of the files that need to be checked
for OTA updates here."""

import os

def get_ota_file_list():
    return [ 'start_up/ota_files.py', # Always include this one
        'start_up/time_functions.py',
        'main.py',
        'lib/senko/senko.py'
        'lib/senko/check_for_updates.py',
        'lib/weather_station/weather_station.py',
        'lib/bmx.py',
        'lib/ntp_clock.py',
        'lib/web_client.py',
        'lib/wifi_connect.py',
        ]