from ssd1306_display.ssd1306_i2c_bl import Display

display = Display()

def receive(lora):
    display.show_text("LoRa Receiver")

    while True:
        if lora.received_packet():
            lora.blink_led()
            print('something here')
            payload = lora.read_payload()
            print(payload)
            display.clear()
            display.show_text(payload)
