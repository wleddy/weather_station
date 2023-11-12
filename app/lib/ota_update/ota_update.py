import urequests
import uhashlib
import gc
import json
from os_path import make_path, exists, join
from logging import logging as log
from settings.settings import settings

gc.enable()

class OTA_Update:
    """Check for updates to the micropython app in the specified files.
    Any files needing updates are placed in a temporary directory.
    It's the responsibility of the calling method to move any changed files into
    their final location.
    
    Args:
        url (str, optional): URL of file repository.
        files (list): Files included in OTA update.
        headers (list, optional): Headers for urequests.
        tmp (str, optional): Start of path to temporary file storage location
    """
    
    def __init__(self,
                 url=None,
                 files=[], 
                 headers={'cache-control':'no-cache'},
                 tmp='/tmp/',
                 ):

        self.url = url if url is not None else settings.ota_source_url
        if not self.url:
            raise ValueError('OTA_Updater.url may not be empty')
            
        self.headers = headers
        self.files = files
        if not isinstance(self.files,list):
            self.files = [self.files]

        self.tmp = tmp
        self.changes = []
        
    
    def _exit():
        # leave because something has gone wrong
        self.changes = []
        return False


    def _hash(self,data):
        if data is None:
            return ''
        
        return str(uhashlib.sha1(data.encode()).digest())
    
    def _get_hash(self):
        return uhashlib.sha1()

    def _get_file(self,filename,local_hash):
        """Post the path of the local file. 
        Server will returnn a json string with the elements:
            hash: sha1 hash string of current file
            file_data: the text of the file
            file_size: size of the file
        else if file not found returns ''
        """
        
        log.debug(f'_get_file {filename}')
        data={'path':filename}
        start = 0
        headers = self.headers
        is_new = True
        while True:
            headers.update({'Range':f'bytes={start}-{start+1024}',})
            payload = urequests.post(self.url, json=data, headers=headers)

            if payload.status_code == 200:
                return_data = json.loads(payload.text)
                file_data = ''
                file_size = 0
                remote_hash = ''
                if 'file_data' in return_data:
                    file_data = return_data['file_data']
                if 'file_size' in return_data:
                    file_size = return_data['file_size']
                if 'hash' in return_data:
                    remote_hash = return_data['hash']

                if not file_data and got_txt == True:
                    return True # got changed file
                if remote_hash != local_hash and file_data:
                    got_txt = True
                    start += len(file_data)
                    self.stash_file(filename,file_data,is_new)
                    is_new = False
                else:
                    return False
            else:
                return False


    def update(self):
        """Determine which files need to be updated
        and place new versions in a temporary directory.
        
        sets self.changes to a list of the files that have updates

        Returns:
            True - if changes were made, False - if not.
        
        """
        
        gc.enable()
        self.changes = []
        
        for file in self.files:
            
            local_hash = None
            local_version = False
            if exists(file):
                log.debug(f'Update: accessing local file {file}')
                with open(file, "r") as local_file:
                    tmp_file = True
                    hasher = self._get_hash()
                    while tmp_file:
                        tmp_file = local_file.read(1024)
                        if tmp_file:
                            hasher.update(tmp_file.encode())
                            local_version = True
                            
                local_hash = str(hasher.digest())
                del hasher, tmp_file
                gc.collect()
            
            remote_version = self._get_file(file,local_hash)
            if remote_version:
                log.info(f'  +++ /{file} needs update')
                self.changes.append(file)
                
        if self.changes:
             return True
        else:
            return False


    def stash_file(self,file,remote_version,new=False):
        # place the new version in the temporary directory
        tmp_path = join('/',self.tmp,file)
        try:
            if make_path(tmp_path):
                mode = 'a'
                if new:
                    mode = 'w'
                with open(tmp_path, mode) as local_file:
                    local_file.write(remote_version)
                # Make a final check that the file exisits in the temp dir
                if not exists(tmp_path):
                    log.error(f'Update: {tmp_path} was not created')
                    self._exit()
            else:
                # we failed
                log.error(f'Update unable to make tmp path to {file}')
                self._exit()
        except Exception as e:
            log.exception(e,f'Update failed to save {file}')
            self._exit()
                    
                    
    


