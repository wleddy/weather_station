
import network
import time

class Wifi_Connect:
    
    def __init__(self,credentials="instance/credentials.conf"):
        self.credentials = credentials
        self.wlan = None
        self.access_point = ""
    
    def connect(self):
        
        # open the credentials file
        # each line contains <ssid,password>
        c = []
        try:
            with open(self.credentials) as f:
                c = f.readlines()
            print("known_ssids:",c)
        except Exception as e:
            print(str(e))
            
        known_ssids = {}
        for x in c:
            l = x.split(",")
            known_ssids[l[0].strip()] = l[1].strip()
            
        # if known_ssids, continue
        if len(known_ssids) > 0:
            # Connect to network
            self.access_point = ""
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            self.wlan.disconnect() # may not be needed

            # scan for available access points
            scan = self._scan()
            # try to find one of our credentals to match
            for ap in scan:
                print("Trying:",ap)
                if ap in known_ssids:
                    # try to connect to this ap
                    print("Connect to {} with key {}".format(ap,known_ssids[ap]))
                    self.wlan.connect(ssid=ap,key=known_ssids[ap])
                    trys = 20
                    while trys > 0 and not self.wlan.isconnected():
                        print(trys,":",self.wlan.status())
                        time.sleep(.5)
                        trys -= 1
                    if self.wlan.isconnected() and self.wlan.status() == network.STAT_GOT_IP:
                        print("Connected. Status:",
                              self.wlan.status())
                        self.access_point = ap
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

        if not self.access_point:
            print("No Access Point Found")
            self.wlan.active(False)
            
                        
    def isconnected(self):
        if not self.wlan:
            return False
        return self.wlan.isconnected()

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

