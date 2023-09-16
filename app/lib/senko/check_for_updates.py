"""Run code to check for updates if available and restart
as needed.
"""
from instance.settings import settings
import machine
from senko import senko
from wifi_connect import connection

class Check_For_Updates:
    
    def __init__(self,display=None, fetch_only=False):
        self.display = display # is there a display to use?
        self.fetch_only = fetch_only # don't actually update any files
        
        self.v_pos = -1 # the screen display if used
        
    def run(self):
        """Update any files that need it..."""
        
        try:
            if not connection.active():
                self.alert('Connecting')
                connection.connect()
        except:
            self.alert('Failed to connect')
            return False
            
        OTA = senko.Senko(
            user="wleddy", repo="weather_station",
            files=[]
            )
        
        # Seems to fail if I try to check more than 3 files in a block
        from start_up.ota_files import get_ota_file_list
        master_list = get_ota_file_list()
                
        self.alert("Checking for updates")
    #     print('file_sets:',file_sets)
        has_changes = False
        for file in master_list: # a list of lists
            OTA.files = [file,]
            self.alert(f'Checking: {file}')
            if self.fetch_only:
                if OTA.fetch():
                    self.alert(f'   --- {file} needs update')
                    has_changes = True
            elif OTA.update():
                has_changes = True
                self.alert(f'   +++ {file} Updated')
            
        self.v_pos = -1 #force screen clear

        if has_changes and self.fetch_only:
                self.alert('Updates are needed')
                return True
        elif has_changes:
            self.alert("Rebooting...")
            machine.reset()
        else:
            self.alert('No update needed')
            return False


    def alert(self,msg):
        type_height = 20 # just to keep it simple
        if self.display:
            if self.v_pos < 0 or self.v_pos + type_height > self.display.MAX_X:
                self.display.clear()
                self.v_pos = 0
            
            self.v_pos += type_height
            self.display.centered_text(msg[-25:],y=self.v_pos,width=self.display.MAX_Y)
            
        else:
            print(msg)



