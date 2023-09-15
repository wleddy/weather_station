
import network
import time
import json

class Wifi_Connect:
    
    def __init__(self,credentials="instance/credentials.conf"):
        self.credentials = credentials
        self.access_point = ""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.disconnect() # may not be needed
    
    def connect(self):
        print('connecting...')
        # try to use last connection
        last_dict = self._last_ssid()
        if last_dict:
            # get the first and only key
            for name in last_dict:
                break # first value is loaded in  name
            
            self._connect_from_list([name],last_dict)

        if not self.access_point:
            print('scan for available access points')
            scan = self._scan()

            # open the credentials file
            # each line contains <ssid,password>
            c = []
            try:
                with open(self.credentials) as f:
                    c = f.readlines()
                print("ssid_credentials:",c)
            except Exception as e:
                print(str(e))
            
            ssid_credentials = {}
            for x in c:
                l = x.split(",")
                ssid_credentials[l[0].strip()] = None #ssid name without password
                if len(l) == 2:
                    # Has password... update value
                    ssid_credentials[l[0].strip()] = l[1].strip()
                
            # if known_ssids, continue
            if len(ssid_credentials) > 0:
                self._connect_from_list(scan,ssid_credentials)

        if not self.access_point:
            print("Unable to connect")
            self.wlan.active(False)
          
    def _last_ssid(self,ssid=None,pw=None):
        """Get or set the last ssid succesfully accessed
        
        always returns a dict
        
        """
        
        if ssid:
            mode = "w"
        else:
            mode = 'r'
 
        out = {}
        
        try:
            with open('/instance/last_ssid.txt',mode) as f:
                if ssid:
                    out = {ssid:pw}
                    f.write(json.dumps(out))
                else:
                    out = json.loads(f.readline())
        except Exception as e:
            print("Unable to access last_ssid: {}".format(str(e)))
            
        return out
    
    
    def _connect_from_list(self,ap_list,ap_credentials):
        """ap_list is a list of ap_names in the order to be tried.
        ap_credentials is a dict as:
        {'ap_name':'ap_password',...}
        """
        
#         # Connect to network
#         self.access_point = ""
#         self.wlan = network.WLAN(network.STA_IF)
#         self.wlan.active(True)
#         self.wlan.disconnect() # may not be needed

        # try to find one of our credentals to match
        for ap in ap_list:
            print("Trying:",ap)
            if ap in ap_credentials:
                # try to connect to this ap
                print("Connect to {} with key {}".format(ap,ap_credentials[ap]))
                self.wlan.connect(ssid=ap,key=ap_credentials[ap])
                trys = 20
                while trys > 0 and not self.wlan.isconnected():
                    print(trys,":",self.wlan.status())
                    time.sleep(.5)
                    trys -= 1
                if self.wlan.isconnected() and self.wlan.status() == network.STAT_GOT_IP:
                    print("Connected. Status:",
                          self.wlan.status())
                    self.access_point = ap
                    #Save credentials for last connection
                    self._last_ssid(ap,ap_credentials[ap])
                    break
                # SSID not connected
                else:
                    print("Connection Failed: ",end="")
                    if self.wlan.status() == network.STAT_NO_AP_FOUND:
                        print("Access Point not found",end="")
                    elif self.wlan.status() == network.STAT_WRONG_PASSWORD:
                        print("Wrong Password",end="")
                    else:
                        print("Unknown Connection Error ({})".format(self.wlan.status()),end="")
                    print()
                    self.wlan.disconnect()

                        
    def isconnected(self):
        if not self.wlan:
            return False
        return self.wlan.isconnected()

    def is_connected(self):
        # should have had this name all along...
        return self.isconnected()

    def disconnect(self):
        if self.wlan:
            self.wlan.disconnect()

    def active(self,state=None):
        if not self.wlan:
            return False
        if state and isinstance(state,bool):
            self.wlan.active(state)
            
        return self.wlan.active()
    
    def status(self):
        if not self.wlan:
            return network.STAT_IDLE
        else:
            return self.wlan.status()

    def _scan(self):
            scan = self.wlan.scan()
            aps_db = []
            aps_names = []
            print("Scan found:",end='')
            for x in range(4):
                scan = self.wlan.scan()
                for s in scan:
                    name = s[0].decode()
                    if name not in aps_names and name != '':
                        aps_names.append(name)
                        x = "000"+str(abs(s[3]))
                        aps_db.append(x[-3:len(x)]+"/"+name) # we want to sort by db
                print(",",len(aps_db),end="")
                time.sleep(1)
                
            print('')
            
            # sort by best signal strength, lowest first
            aps_db.sort()
            print("Scaned:",aps_db)
            scan=[]
            for l in aps_db:
                scan.append(l.split('/')[1])
                
            return scan

