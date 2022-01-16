# set up for spi bus and ITF display

from machine import Pin, SoftSPI
from ili9341 import Display

def get_spi():
#     spi = SoftSPI(baudrate=40000000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
    spi = SoftSPI(baudrate=40000000, sck=Pin(18), mosi=Pin(19), miso=Pin(23))

    return spi


def get_display(spi,**kwargs):
#     display = Display(spi, dc=Pin(4), cs=Pin(5), rst=Pin(18))
#     display = Display(spi, dc=Pin(33), cs=Pin(5), rst=Pin(15),rotation=180)
    rotation = 0
    if 'rotation' in kwargs:
        rotation = kwargs['rotation']
        
    display = Display(spi, dc=Pin(33), cs=Pin(5), rst=Pin(15),rotation=rotation)
    return display


def setup(**kwargs):
    spi = get_spi()
    display = get_display(spi,**kwargs)
    
    return spi, display


