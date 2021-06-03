# set up the LoRa Radio

from machine import Pin, SPI
from lora.lora_config import * #import the pin configuration
from lora.sx127x import SX127x
from time import sleep


class LoRaRadio:
    def __init__(self,spi,ss):
        self.lora = SX127x(spi,ss,pins=device_config, parameters=lora_parameters)
        self.lora.set_spreading_factor(12) #Max Range
        
        
    def receive(self,display=None):
        last = 0
        missed = 0
        if display:
            display.show_text("LoRa Receiver")

        while True:
            if self.lora.received_packet():
#                 self.lora.blink_led()
                print('something here')
                payload = self.lora.read_payload()
                print(payload)
                this = payload.decode('utf-8').strip().split(': ')
                if isinstance(this,list) and len(this) > 1:
                    try:
                        this = int(this[1])
                    except ValueError:
                        this = last
                        missed += 1
                    except Exception as e:
                        print('Error: {}'.format(str(e)))
                        if display:
                            display.clear()
                            display.show_text(str(e))
                            display.show_text(payload,y=12)

                        sleep(30)
                        this = last
                        missed += 1
                else:
                    this = last
                    missed += 1
                            
                if last > 0 and this > last + 1:
                    missed = missed + (this - last)
                last = this
                if display:
                    display.clear()
                    display.show_text(payload)
                    #display.show_text("Missed: {}".format(missed),y=12)
                    display.show_text("RSSI: {}".format(self.lora.packet_rssi()),y=24)
            
            # take a break till next read attempt...
            sleep(.25)
            
                    
    def send(self,display=None,scan_tags=True):
        if scan_tags:
            try:
                from rfid.rfid_simple_reader import scan
            except ImportError:
                pass
        
        counter = 0
        print("LoRa Sender")
        if display:
            display.show_text("LoRa Sender")
            sleep(1)

        while True:
            payload = ''
            try:
                if scan_tags:
                    payload = scan() + ' : ' + str(counter)
                else:
                    payload = "Counter: {}".format(counter)
            except Exception as e:
                print('scan not available: {}'.format(str(e)))
                
            if payload:
                print("Sending packet: \n{}\n".format(payload))
                if display:
                    display.clear()
                    display.show_text('Sending Packet...')
                    display.show_text(payload,y=12)
#                     display.show_text("RSSI: {}".format(self.lora.packet_rssi()),y=24)
#                     display.show_text("Counter: {}".format(counter),y=36)
                    
                self.lora.println(payload)

                counter += 1
                sleep(1)
