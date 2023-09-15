"""Run code to check for updates if available and restart
as needed.
"""
from instance.settings import settings
import machine
from senko import senko
from wifi_connect import Wifi_Connect
import time

def run():
    #   url='https://github.com/wleddy/weather_station/tree/master/app/'

 
    settings.wlan = Wifi_Connect()
    settings.wlan.connect()
    
    if not settings.wlan.is_connected():
        return
        
    OTA = senko.Senko(
        user="wleddy", repo="weather_station",
        files=[]
        )
    
    # Seems to fail if I try to check more than 3 files in a block
    from start_up.ota_files import get_ota_file_list
    master_list = get_ota_file_list()
    
    # break up the master list into managable chunks
    file_sets = []
    while master_list:
        temp_list = []
        for i in range(2):
            if len(master_list) > 0:
                temp_list.append(master_list.pop(0))
        if temp_list:
#             print('temp_list:',temp_list)
            file_sets.append(temp_list)
            
    print("Checking for updates")
#     print('file_sets:',file_sets)
    changed_files = []
    for set in file_sets: # a list of lists
        
        print('Checking set:',set)
        OTA.files = set
        changed_files.append(OTA._check_all())
        print('{} Changes'.format(len(changed_files)))
          
    has_changes = False
    for set in changed_files: # this is a list of list
        if set:
            OTA.files = set
            has_changes = True
            print('Updating:',OTA.files)
            OTA.update()
        
    if has_changes:
        print("Updated to the latest version! Rebooting...")
        machine.reset()
    else:
        print('No update needed')
