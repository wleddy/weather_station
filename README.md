# weather_station

A Micropython project to create a simple remote weather station using a BMP280 sensor and LoRa radios.


## Hardware:


### I2C: 

BMP setup to use I2C communication. Uses pin 4 for sda, and pin 15 for scl.
The BMP is powered from GIO pin 17 so that it can be turned off when not 
needed.

The address for the BMX is 118 digital.



VCC for BMP is 3.3V
