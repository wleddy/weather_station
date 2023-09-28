"""Run code to check for updates if available and restart
as needed.
"""

from instance.settings import settings
import machine
from senko import senko
from start_up.ota_files import get_ota_file_list
from wifi_connect import connection
from file_utils import make_path, delete_all

class Check_For_Updates:
    
    def __init__(self,user=None, repo=None, display=None, fetch_only=False):
        self.display = display # is there a display to use?
        # set fetch_only True to skip the update operation
        #   set settings.fetch_only = True in main.py to run tests 
        #   without actually updating
        if fetch_only: 
            self.fetch_only = fetch_only 
        else: 
            self.fetch_only = getattr(settings,'fetch_only',False)
        
        # don't actually run the update process
        self.defer_update = getattr(settings,'defer_update',False)
        
        self.v_pos = -1 # the screen display if used
        self.changes = [] #paths to updated files
        self.tmp='/tmp/'
        
        if not user: user = settings.OTA_info['user']
        if not repo: repo = settings.OTA_info['repo']

        branch = 'master'
        b = getattr(settings,'OTA_info',{})
        if 'branch' in b:
            branch = b['branch']
            
        self.OTA = senko.Senko(
            user=user, repo=repo,
            files=[],
            branch=branch
            )
        self.OTA.tmp = self.tmp
 

    def run(self):
        """Update any files that need it..."""
        
        if self.defer_update:
            self.alert('Updates Deferred')
            return False
        
        try:
            if not connection.is_connected():
                self.alert('Connecting')
                connection.connect()
        except:
            self.alert('Failed to connect')
            return False
                   
        file_list = get_ota_file_list()
                
        self.alert("Checking for updates")
        if self.fetch_only:
            self.alert('--- Fetch Only ---')

        has_changes = False
        changes = []

        for file in file_list: 
            # test one file at a time
            # each file will be saved to a temporary location
            # and moved into the final location after all changed
            # new files have been successully downloaded.
            self.OTA.files = [file,]
            self.alert(f'Checking: {file}')
            if self.fetch_only:
                if self.OTA.fetch():
                    self.alert(f'   --- {file} needs update')
                    has_changes = True
            elif self.OTA.update():
                has_changes = True
                changes.append(file)
                self.alert(f'   +++ {file} Updated')
            
        self.v_pos = -1 #force screen clear

        if has_changes and self.fetch_only:
                self.alert('Updates are needed')
                return True
        elif has_changes and changes:
            self.alert('Downloads successful')
            self.alert('Moving files')
            for file in changes:
                # build the path to the new file if needed
                if make_path(file):
                    #path should now exist
                    try:
                        tmp_file = open(self.tmp + '/' + file, "r")
                        local_file =  open(file, "w")
                        local_file.write(tmp_file.read())
                    except:
                        self.alert('Move Failed')
                        print('Unable to move temp file:',file)
                    finally:
                        local_file.close()
                        tmp_file.close()

            delete_all(self.tmp)
            self.v_pos = -1 #force screen clear
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

