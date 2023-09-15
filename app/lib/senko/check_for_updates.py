"""Run code to check for updates if available and restart
as needed.
"""
from instance.settings import settings
import machine
from senko import senko
from wifi_connect import Wifi_Connect

def run():
    """Update any files that need it..."""
    try:
        settings.wlan = Wifi_Connect()
        settings.wlan.connect()
        if not settings.wlan.is_connected():
            return
    except:
        return
        
    OTA = senko.Senko(
        user="wleddy", repo="weather_station",
        files=[]
        )
    
    # Seems to fail if I try to check more than 3 files in a block
    from start_up.ota_files import get_ota_file_list
    master_list = get_ota_file_list()
            
    print("Checking for updates")
#     print('file_sets:',file_sets)
    has_changes = False
    for file in master_list: # a list of lists
        OTA.files = [file,]
        print('Checking:',file)
        if OTA.update():
            has_changes = True
            print(f'   +++ {file} Updated')
        
    if has_changes:
        print("Updated to the latest version! Rebooting...")
        machine.reset()
    else:
        print('No update needed')







