"""Run code to check for updates if available and restart
as needed.
"""

from instance.settings import settings
import machine
from senko import senko
from start_up.ota_files import get_ota_file_list
from wifi_connect import connection

class Check_For_Updates:
    
    def __init__(self,display=None, fetch_only=False):
        self.display = display # is there a display to use?
        # set fetch_only True to skip the update operation
        #   set settings.fetch_only = True in main.py to run tests 
        #   without actually updating
        self.fetch_only = getattr(settings,'fetch_only',fetch_only)
        
        # don't actually run the update process
        self.defer_update = getattr(settings,'defer_update',False)
        
        self.OTA = None
        self.v_pos = -1 # the screen display if used
        
        
    def run(self):
        """Update any files that need it..."""
        
        if self.defer_update:
            self.alert('Updates Deferred')
            return False
        
        try:
            if not connection.active():
                self.alert('Connecting')
                connection.connect()
        except:
            self.alert('Failed to connect')
            return False
            
        self.OTA = senko.Senko(
            user=settings.OTA_info['user'], repo=settings.OTA_info['repo'],
            files=[]
            )
        
        # Seems to fail if I try to check more than 3 files in a block
        file_list = get_ota_file_list()
                
        self.alert("Checking for updates")
        if self.fetch_only:
            self.alert('--- Fetch Only ---')
    #     print('file_sets:',file_sets)
        has_changes = False
        for file in file_list: # a list of lists
            self.OTA.files = [file,]
            self.alert(f'Checking: {file}')
            if self.fetch_only:
                if self.OTA.fetch():
                    self.alert(f'   --- {file} needs update')
                    has_changes = True
            elif self.OTA.update():
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

