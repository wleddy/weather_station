# weather_station

A Micropython project to create a simple temperature display using two BMP280 sensors.

This version is set up for the Raspberry Pi Pico W with wireless connection. Currently only uses
the wireless connection to get the current time from a ntp service. The idea is to display the time
as well as the temperatre. 

## Hardware:

### Processor: Raspberry Pi Pico W

### I2C Temperature sensors: 

The BMP setup uses two sensor devices connect via I2C. I'm making use of the 2 hardware I2C channels
to get around the fact that the units I have have a fixed address of 118 digital. 

### iLi9341 Display driver

The display is a 240 X 320px TFT display connected via the SPI bus.

## Display Images:

The digits that are the primary display elements are rendered from image file rather than TFT fonts.

The initial version had only two temperature lines plus a descriptive line for each. The digit images
were generally 80 X 48px but some of the narrow elements were narrower.

For this version the images will need to be reduced to 60px X 36px.

For use with the display the images created in png format need to be converted to the .raw format using the
python script img2rgb565.py.

## Proof it worked...

![Image](images/pic.jpg)

