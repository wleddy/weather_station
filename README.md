# weather_station

A Micropython project to create a simple remote weather station using a BMP280 sensor and LoRa radios.

As it turned out... the battery life for the remote LoRa unit was not what I'd hoped for so I just
wired the remote BME unit to the main board and lead it out the window...

## Hardware:


### I2C: 

BMP setup to use I2C communication. Uses pin 4 for sda, and pin 15 for scl.
The BMP is powered from GIO pin 17 so that it can be turned off when not 
needed.

The address for the BMX is 118 digital.

In order to switch between the 2 BME units with the same address I used a PNP transister attached to
the SDA line of the indoor sensor and a NPN transister attached to the SDA line of the outdoor sensor
with their bases wired together so that when one transistor is not conducting the other will be. All the 
other lines of the 2 sensors are tied together.

## Proof it worked...

![Image](images/pic.jpg)

