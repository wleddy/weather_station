# set up for spi bus and ITF display

from machine import Pin, SoftSPI
from ili9341 import Display

        #spi = SoftSPI(baudrate=20000000, sck=Pin(5), mosi=Pin(19), miso=Pin(27))
        
        #display = Display(spi, dc=Pin(4), cs=Pin(21), rst=Pin(23))

def get_spi():
    spi = SoftSPI(baudrate=40000000, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
    return spi


def get_display(spi):
    display = Display(spi, dc=Pin(21), cs=Pin(13), rst=Pin(23))
    return display


def setup():
    spi = get_spi()
    display = get_display(spi)
    
    return spi, display

