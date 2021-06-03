# Set up the pins to use for the SPI bus
from machine import Pin, SPI
import spi_setup.spi_config as spi_config

def get_spi(device_type=None,sck=None,mosi=None,miso=None,ss=None):
    # device_type is a predfined shortcut for the device
    config = None
    if device_type:
        config = spi_config.device_types.get(device_type)
    if not config:
        config = spi_config['default_device']
    
    print(config)
    
    if not sck:
        sck = config['sck']
    if not mosi:
        mosi = config['mosi']
    if not miso:
        miso = config['miso']
    if not ss:
        ss = config.get('ss') ## ss may be None for now
        
    spi = SPI(baudrate = 1000000, 
        polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB,
        sck = Pin(sck, Pin.OUT, Pin.PULL_DOWN),
        mosi = Pin(mosi, Pin.OUT, Pin.PULL_UP),
        miso = Pin(miso, Pin.IN, Pin.PULL_UP))

    return spi, ss