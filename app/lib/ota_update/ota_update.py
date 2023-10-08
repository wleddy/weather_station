import urequests
import uhashlib
import gc
from os_path import make_path, exists, join
from settings.settings import settings, log

gc.enable()

class OTA_Update:
    """Check for updates to the micropython app in the specified.
    
    As a matter of policy, don't try to catch any errors here. Catch
    them in the calling method to make connection debugging easier.
    
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
        
    
    def _hash(self,data):
        if data is None:
            return ''
        
        return str(uhashlib.sha1(data.encode()).digest())
    
    
    def _check_hash(self, x, y):
        if x is None or y is None:
            return True
        
        x_hash = uhashlib.sha1(x.encode())
        y_hash = uhashlib.sha1(y.encode())

        x = x_hash.digest()
        y = y_hash.digest()

        out = False
        if str(x) == str(y):
            out = True
            
        return out


    def _get_file(self, url):
        log.debug(f'_get_file {url}')
        gc.collect()
        payload = urequests.get(url, headers=self.headers)
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
            log.info(f'Update: accessing remote file {file}')
            latest_version = self._get_file(self.url + "/" + file)
            self.stash_file(file,latest_version)
            latest_hash = self._hash(latest_version)
            
            if latest_version is None:
                # a file does not exist on the server.
                # we may want to delete the local version
                log.info(f'Update: file {file} not found on server')
                continue
            
            del latest_version
            gc.collect()

            local_version = None
            if exists(file):
                log.info(f'Update: accessing local file {file}')
                with open(file, "r") as local_file:
                    local_version = local_file.read()
                    local_hash = self._hash(local_version)
                
#             if not self._check_hash(latest_version, local_version) \
            if not latest_hash == local_hash \
                or (local_version is None):
                log.info(f'  +++ /{file} needs update')
                self.changes.append(file)
                
            del local_version
            gc.collect()
                
    def stash_file(self,file,latest_version):
        # place the new version in the temporary directory
        tmp_path = join(self.tmp,file)
        try:
            if make_path(tmp_path):
                with open(tmp_path, "w") as local_file:
                    local_file.write(latest_version)
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
                    
                    
        if self.changes:
             return True
        else:
            return False
        
        def _exit():
            # leave this module because something has gone wrong
            self.changes = []
            return False
    

