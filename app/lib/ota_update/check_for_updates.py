"""Run code to check for updates if available and restart
as needed.
"""

from wifi_connect import connection
if connection.wifi_available:
    from ota_update.ota_update import OTA_Update
from logging import logging as log
from settings.settings import settings
import machine
from settings.ota_files import get_ota_file_list
from os_path import make_path, delete_all, join, exists
import os


class Check_For_Updates:
    """Calls ota_update to check for any files that have updates.
        ota_update will place the changed files in a temporary directory.
        
        If all changed files were downloaded successfully, move them into
        their final location and reboot the device.
        
        If updates were installed, return True.
        """
    
    def __init__(self, display=None, fetch_only=None):
        self.display = display # is there a display to use?
        #   set settings.fetch_only = True in main.py to run tests 
        #   without actually updating
        self.fetch_only = getattr(settings,'fetch_only',False)
        if fetch_only is not None: 
            self.fetch_only = fetch_only 
        
        self.tmp='/tmp/'
        self.file_list = []
        self.changes = []

    def run(self):
        """Update any files that need it..."""
        connection.connect()
        if  not connection.is_connected():
            log.info('Failed to connect')
            return False
                   
        self.file_list = get_ota_file_list()
                
        log.info("Checking for updates")
        log.info(f'URL : {settings.ota_source_url}')
        if self.fetch_only:
            log.info('--- Fetch Only ---')
        
        delete_all(self.tmp)
                
        # First check 'settings/ota_files.py' to see if it needs update
        # If so, install that first, and reboot
        log.info('Checking ota_files')
        ota = OTA_Update(files=['settings/ota_files.py'],tmp=self.tmp)
        ota.update()
                        
        if ota.changes:
            return self.install_updates(ota.changes)

        # If we got this far, run the full update
        ota = OTA_Update(files=self.file_list,tmp=self.tmp)
        ota.update()
        self.changes.extend(ota.changes)
                        
        if self.changes:
            log.info('{} files ready to update'.format(len(self.changes)))
            log.info('Updating: {}'.format(', '.join(self.changes)))
            return self.install_updates(self.changes)
        else:
            log.info('No updates needed')
            return False                

    def install_updates(self,changes):
        """Move files from the temporary directory into final location.
        Return False if not able to complete all moves."""
        
        log.info('Installing updated files')
        for file in changes:
            # build the path to the new file if needed
            file = join('/',file)
            tmp_file = join('/',self.tmp,file)
            if make_path(file):
                #path should now exist
                
                try:
                    if not self.fetch_only:
                        if exists(file):
                            os.remove(file)
                        os.rename(tmp_file,file)
                        log.info(f'moved {file}')
                    else:
                        log.info(f'fetch only: {file}')
                except Exception as e:
                    log.error(f'file {file} was not in tmp dir')
                    log.exception(e,'Update aborted')
                    return False
            else:
                log.info(f'Could not make path for {file}')
                return False
        
        if not self.fetch_only:
            delete_all(self.tmp)
            log.info("Rebooting...")
            machine.reset()
        
