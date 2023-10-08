"""Run code to check for updates if available and restart
as needed.
"""

from settings.settings import settings, log
import machine
from ota_update.ota_update import OTA_Update
from settings.ota_files import get_ota_file_list
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
        
        self.tmp='/tmp/'
        self.file_list = []

    def run(self):
        """Update any files that need it..."""
        connection.connect()
        if not connection.is_connected():
            log.info('Failed to connect')
            return False
                   
        self.file_list = get_ota_file_list()
                
        log.info("Checking for updates")
        log.info(f'URL : {settings.ota_source_url}')
        if self.fetch_only:
            log.info('--- Fetch Only ---')
        
        delete_all(self.tmp)
        
        # First check 'settings/ota_files.py' to see if it needs update
        # If so, install that first then come back and do the rest
        log.info('Checking "settings/ota_files.py"')
        ota = OTA_Update(files=['settings/ota_files.py'],tmp=self.tmp)
        ota.update()
                        
        if ota.changes:
            if self.fetch_only:
                return True
            else:
                self.install_updates(ota.changes)


        ota = OTA_Update(files=self.file_list,tmp=self.tmp)
        ota.update()
                    
        log.info('{} files ready to update'.format(len(ota.changes)))
        log.info('Updating: {}'.format(', '.join(ota.changes)))
        
        if self.fetch_only:
            return True
                
        if ota.changes:
            self.install_updates(ota.changes)
        else:
            log.info('No update needed')
            return False                

    def install_updates(self,changes):
        log.info('Moving files')
        for file in changes:
            # build the path to the new file if needed
            file = join('/',file)
            if make_path(file):
                #path should now exist
                log.info(f'file: {file} being moved')
                tmp_file = open(join(self.tmp,file), "r")
                local_file =  open(file, "w")
                local_file.write(tmp_file.read())

                local_file.close()
                tmp_file.close()
            else:
                log.info(f'Could not make path for {file}')
                return False
        
        if not settings.debug:
            delete_all(self.tmp)
        log.info("Rebooting...")
        machine.reset()
        
