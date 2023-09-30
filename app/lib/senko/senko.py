import urequests
import uhashlib
import gc
from file_utils import make_path

class Senko:
    raw = "https://raw.githubusercontent.com"
    github = "https://github.com"

    def __init__(self, user, repo, 
                 url=None, branch="master", 
                 working_dir="app", 
                 files=["boot.py", "main.py"], 
                 headers={'cache-control':'no-cache'},
                 tmp='/tmp/',
                 ):
        """Senko OTA agent class.

        Args:
            user (str): GitHub user.
            repo (str): GitHub repo to fetch.
            branch (str): GitHub repo branch. (master)
            working_dir (str): Directory inside GitHub repo where the micropython app is.
            url (str): URL to root directory.
            files (list): Files included in OTA update.
            headers (list, optional): Headers for urequests.
            tmp (str): Start of path to temporary file storage location
        """
        self.base_url = "{}/{}/{}".format(self.raw, user, repo) if user else url.replace(self.github, self.raw)
        self.url = url if url is not None else "{}/{}/{}".format(self.base_url, branch, working_dir)
        self.headers = headers
        self.files = files
        self.tmp = tmp

    def _check_hash(self, x, y):        
        x_hash = uhashlib.sha1(x.encode())
        y_hash = uhashlib.sha1(y.encode())

        x = x_hash.digest()
        y = y_hash.digest()

        if str(x) == str(y):
            out = True
        else:
            out = False
            
        del(x,y,x_hash,y_hash)
        return out

    def _get_file(self, url):
        try:
            payload = urequests.get(url, headers=self.headers)
            code = payload.status_code
            if code == 200:
                return payload.text
            else:
                return None
        except Exception as e:
            print('Error getting file:',str(e))
            return None
        

    def _check_all(self):
        changes = []
        
        for file in self.files:
            gc.enable()
            gc.collect()
            try:
                latest_version = self._get_file(self.url + "/" + file)
            except Exception as e:
                print('failed to get file from github:',str(e))
                return False
            
            if latest_version is None:
                continue

            try:
                with open(file, "r") as local_file:
                    local_version = local_file.read()
            except:
                local_version = ""
                
            if local_version and latest_version and \
                not self._check_hash(latest_version, local_version):
                changes.append(file)

        return changes

    def fetch(self):
        """Check if newer version is available.

        Returns:
            True - if is, False - if not.
        """
        if not self._check_all():
            return False
        else:
            return True

    def update(self):
        """Replace all changed files with newer one.

        Returns:
            True - if changes were made, False - if not.
        
        Initally save files to a temporary dir and move them if
        all downloads are successfull.
        """
        
        changes = self._check_all()
        
        for file in changes:
            # build the path to the new file if needed
            if make_path(self.tmp + file):
                #path should now exist
                try:
                    local_file =  open(self.tmp + '/' + file, "w")
                    local_file.write(self._get_file(self.url + "/" + file))
                except Exception as e:
                    # unable to write tmp file
                    changes = []
                    print('Unable to save temp file:',file)
                    print('Error:',str(e))
                finally:
                    local_file.close()

            else:
                # Not able to update one of the files, so give up
                changes = [] # will return False
                break
                

        if changes:
             return True
        else:
            return False