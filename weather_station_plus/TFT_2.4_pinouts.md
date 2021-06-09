# Pin outs for 2.2" TFT SPI Display

ILI9341 device

Pin 1 is in the top right when viewing the board from the display side.

'mosi': 27, 'sck': 5, 'miso': 19, 'reset': 14, 'led': 2, 'ss': 18, 'dio_0': 26}

Display board           ESP32 (TTGO)
* Touch group *      
1. T_IRQ                
2. T_OUT                
3. T_DIN                
4. T_CS              
5. T_CLK                
* SPI group *          
6. SDO / MISO           19
7. LED - 3v3            34
8. SCK                  5
9. SDI / MOSI           27
10. D/C - Data/Cmd      21 
11. RESET               23
12. CS                  13
13. GND                 GND
14. VCC - 3v3           3v3

