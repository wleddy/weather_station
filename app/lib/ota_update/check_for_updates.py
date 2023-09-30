"""Run code to check for updates if available and restart
as needed.
"""

from instance.settings import settings
import machine
from ota_update.ota_update import OTA_Update
from start_up.ota_files import get_ota_file_list
from wifi_connect import connection
from os_path import make_path, delete_all, join

class Check_For_Updates:
    
    def __init__(self, display=None, fetch_only=False):
        self.display = display # is there a display to use?
        # set fetch_only True to skip the update operation
        #   set settings.fetch_only = True in main.py to run tests 
        #   without actually updating
        if fetch_only: 
            self.fetch_only = fetch_only 
        else: 
            self.fetch_only = getattr(settings,'fetch_only',False)
        
        self.v_pos = -1 # the screen display if used
        self.changes = [] #paths to updated files
        self.tmp='/tmp/'
        self.file_list = []

    def run(self):
        """Update any files that need it..."""
        try:
            connection.connect()
        except:
            self.alert('Failed to connect')
            return False
                   
        self.file_list = get_ota_file_list()
                
        self.alert("Checking for updates")
        self.alert(f'URL : {settings.ota_source_url}')
        if self.fetch_only:
            self.alert('--- Fetch Only ---')
        
        delete_all(self.tmp)
        ota = OTA_Update()
        updates = []
        for file in self.file_list:
            ota.files=[file]
            if ota.update():
                if not ota.changes:
                    continue
                updates.append(file)
                self.alert(f'  +++ /{file} needs update')
                    
        self.alert('{} files ready to update'.format(len(updates)))
                    
        if self.fetch_only:
            return True
                
        self.alert('Downloads successful')
        self.alert('Moving files')
        for file in updates:
            # build the path to the new file if needed
            file = join('/',file)
            if make_path(file):
                #path should now exist
                    print(f'file: {file} being moved')
#                     try:
                    tmp_file = open(join(self.tmp,file), "r")
                    local_file =  open(file, "w")
                    local_file.write(tmp_file.read())
#                     except:
                    # self.alert('Move Failed')
                    # print('Unable to move temp file:',file)
#                     finally:
                    local_file.close()
                    tmp_file.close()
            else:
                self.alert('No update needed')
                return False

            delete_all(self.tmp)
            self.v_pos = -1 #force screen clear
            self.alert("Rebooting...")
            machine.reset()
                

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

