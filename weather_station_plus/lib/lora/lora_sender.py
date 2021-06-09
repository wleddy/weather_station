from time import sleep
from ssd1306_display.ssd1306_i2c_bl import Display
from rfid.rfid_simple_reader import scan

def send(lora):
    counter = 0
#     print("LoRa Sender")
    display = Display()
    display.show_text("LoRa Sender")
    sleep(1)

    while True:
        payload = scan() + ' : ' + str(counter)
#         payload = 'Hello ({0})'.format(counter)
#         print("Sending packet: \n{}\n".format(payload))
        display.clear()
        display.show_text('Sending Packet...')
        display.show_text(payload,y=12)
        display.show_text("RSSI: {}".format(lora.packet_rssi()),y=24)
        display.show_text("Counter: {}".format(counter),y=36)
        lora.println(payload)

        counter += 1
        sleep(1)