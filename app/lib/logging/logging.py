import sys
import time
import os
import os_path
import gc
try:
    import urequests
except ImportError:
    pass
    
import json

CRITICAL = const(50)
ERROR = const(40)
WARNING = const(30)
INFO = const(20)
DEBUG = const(10)
NOTSET = const(0)

_level_str = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG"
}

_stream = sys.stderr  # default output
_filename = '/log.log'  # overrides stream
_level = INFO  # ignore messages which are less severe
_format = "%(asctime)s:%(levelname)s:%(message)s"  # default message format
_loggers = dict()


class Logger:

    def __init__(self, name):
        self.name = name
        self.level = _level

    def _get_log_str(self,level,message,*args):
        try:
            if args:
                message = message % args

            record = dict()
            record["levelname"] = _level_str.get(level, str(level))
            record["level"] = level
            record["message"] = message
            record["name"] = self.name
            tm = time.localtime()
            record["asctime"] = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}" \
                .format(tm[0], tm[1], tm[2], tm[3], tm[4], tm[5])

            return _format % record + "\n"
        except Exception as e:
           # sometimes the message is not a compatible str object
           message = f"Invalid message. Exception: {str(e)}"
           self._get_log_str(level,message,*args)
    
        
    def log(self, level, message, *args):
        gc.collect()
        if level < self.level:
            return

        try:
            error_text = ''
            err = None
            
            log_str = self._get_log_str(level,message,*args)

            if _filename is None:
                _ = _stream.write(log_str)
            else:
                try:
                    from settings.settings import settings
                    from wifi_connect import connection
                    if connection.is_connected() and settings.log_export_url:
                        urequests.post(settings.log_export_url,data=json.dumps({'device_id':settings.device_id,'log':log_str}))
                except ImportError:
                    # Settings and wifi_connect may try to log something before they're setup
                    pass
                except Exception as e:
                    if 'EHOSTUNREACH' not in str(e): # most likely don't have a connection
                        # log the error even thou it probably can't be sent to server...
                        err = e
                        error_text = self._get_log_str(level,f"Log post error: {str(e)}")

                prune(_filename)
                
                with open(_filename, "a") as fp:
                    fp.write(log_str)
                    if error_text:
                        fp.write(error_text)
                        sys.print_exception(err, fp)
                        message += '\n' + error_text # this will print out if in debug
                                                
                # Allways print out the log message when in debug
                if self.level == DEBUG:
                    print(message)
                            
        except OSError as e:
            # Check if flash is full
            if int(os_path.flash_stats()['free'] ) < 1024:
                # clear the log file
                open(filename,'w').close()
                self.log(self.DEBUG,'____ Flash was full. Log purged _____')

        except Exception as e:
            print("--- Logging Error ---")
            print(repr(e))
            print("Message: '" + message + "'")
            print("Arguments:", args)
            print("Format String: '" + _format + "'")
            
            if self.level >= DEBUG:
                raise e

    def setLevel(self, level):
        self.level = level

    def debug(self, message, *args):
        self.log(DEBUG, message, *args)

    def info(self, message, *args):
        self.log(INFO, message, *args)

    def warning(self, message, *args):
        self.log(WARNING, message, *args)

    def error(self, message, *args):
        self.log(ERROR, message, *args)

    def critical(self, message, *args):
        self.log(CRITICAL, message, *args)

    def exception(self, exception, message, *args):
        # if seetings is debug and there is a file, print the message
        self.log(ERROR, message, *args)

        if _filename is None or self.level == DEBUG:
            sys.print_exception(exception, _stream)
            
        if not _filename is None:
            with open(_filename, "a") as fp:
                sys.print_exception(exception, fp)
                

def getLogger(name="root"):
    if name not in _loggers:
        _loggers[name] = Logger(name)
    return _loggers[name]


def basicConfig(level=INFO, filename=None, filemode='a', format=None):
    global _filename, _level, _format
    _filename = filename
    _level = level
    if format is not None:
        _format = format

    if filename is not None and filemode != "a":
        with open(filename, "w"):
            pass  # clear log file


def setLevel(level):
    getLogger().setLevel(level)

huh = 'Undefined Message' # just to avoid error if no message provided

def debug(message=huh, *args):
    getLogger().debug(message, *args)


def info(message=huh, *args):
    getLogger().info(message, *args)


def warning(message=huh, *args):
    getLogger().warning(message, *args)


def error(message=huh, *args):
    getLogger().error(message, *args)


def critical(message=huh, *args):
    getLogger().critical(message, *args)


def exception(exception, message=huh, *args):
    getLogger().exception(exception, message, *args)
    
def prune(filename):
    # reduce log file to no more than
    try:
        stat = os_path.flash_stat(filename)
        size = stat['size'] #file size in bytes
        free = stat['free'] #all free space
        prune_size = int(size * 0.66) # reduce by 1/3 if needed
        tmp_file = filename + 'tmp'
#         print('size',size,'prune to',prune_size,'free',free)
        if size > free * 0.5:
            with open(filename,'r') as old:
                with open(tmp_file,'w') as new:
                    new.write('------------- pruned ----------------\n')
                    old.seek(size - prune_size)
                    old.readline() #consume any left over for line
                    x = True
                    while x:
                        x = old.readline()
                        if x:
                            new.write(x)
                            
            # swap files
            os.remove(filename)
            os.rename(tmp_file,filename)
            
    except OSError as e:
        # just empty the files
        open(filename,'w').close()
        info(f'File purge failed: {str(e)}')
        
    except Exception as e:
        # logging this may cause an infinate loop
        print(f'Exception pruning log: {str(e)}')
        
        
