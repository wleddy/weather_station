import urequests
import uhashlib
import gc
from os_path import make_path, exists, join
from settings.settings import settings, log

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
    

    def _check_file(self,filename,local_hash):
        """Post the local filename (path, really) and the hash
        of that file. Server will compare hash with server's version
        and return the server copy of the file if different or
        the empty string if the hashs match."""
        
        log.debug(f'_check_file {filename}')
        data={'filename':filename,'local_hash':local_hash}
        payload = urequests.post(self.url, json=data, headers=self.headers)
        code = payload.status_code
        log.debug(f'_get_file status code: {code}')
        if code == 200:
            return payload.text
        else:
            return None


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
                    local_version = local_file.read()
                    local_hash = self._hash(local_version)
                local_version = True
                gc.collect()
                
            remote_version = self._check_file(file,local_hash)
            if remote_version:
                log.info(f'  +++ /{file} needs update')
                self.stash_file(file,remote_version)
                del remote_version
                gc.collect()
                
                self.changes.append(file)
                                
        if self.changes:
             return True
        else:
            return False


    def stash_file(self,file,remote_version):
        # place the new version in the temporary directory
        tmp_path = join('/',self.tmp,file)
        try:
            if make_path(tmp_path):
                with open(tmp_path, "w") as local_file:
                    local_file.write(remote_version)
                # Make a final check that the file exisits in the temp dir
                if not exists(tmp_path):
                    log.error(f'Update: {tmp_path} was not created')
                    _exit()
            else:
                # we failed
                log.error(f'Update unable to make tmp path to {file}')
                _exit()
        except Exception as e:
            log.exception(e,f'Update failed to save {file}')
            _exit()
                    
                    
    

