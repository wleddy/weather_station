"""Keep a list of the files that need to be checked
for OTA updates here."""

import os

def get_ota_file_list():
    return [ 'settings/ota_files.py', # Always include this one
        'settings/time_functions.py',
        'settings.credentials.conf',
        'settings.settings.py',
        'settings.calibration_sata.py',
        'main.py',
        'lib/ota_update/ota_update.py',
        'lib/ota_update/check_for_updates.py',
        'lib/weather_station/weather_station.py',
        'lib/bmx.py',
        'lib/ntp_clock.py',
        'lib/web_client.py',
        'lib/wifi_connect.py',
        'lib/os_path.py',
        ]