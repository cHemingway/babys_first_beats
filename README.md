## Baby's First Beats

Sample box for a very small child, to introduce them to DnB/Garage/Jungle etc

### Hardware
- [Adafruit RP2040 Prop-Maker Feather](https://learn.adafruit.com/adafruit-rp2040-prop-maker-feather)
    - Modified to remove 10K pullup on EN pin
- [Mini speaker 4R 3W](https://shop.pimoroni.com/products/mini-speaker-4-3w)
- [2200mAh LiPo battery pack](https://shop.pimoroni.com/products/lithium-ion-battery-pack?variant=23417820359)
- [Colourful Arcade Buttons](https://shop.pimoroni.com/products/colourful-arcade-buttons?variant=451785353)
- 3D Printed Case, see /cad
- [Adafruit Micro SD SPI or SDIO Card Breakout Board - 3V ONLY!](https://www.adafruit.com/product/4682)
- [Adafruit Push Button Power Switch Breakout](https://www.adafruit.com/product/1400) Drives EN pin high to latch power on

### Code
- Runs on CircuitPython 9.0
- Hardware test project in `code/hw_test` 

### Samples
- https://www.reddit.com/r/Drumkits/comments/h9o71o/remeber_the_dj_button_on_the_keyboards_in_school/
- https://www.reddit.com/r/Drumkits/comments/lug5zw/0gjungle_warfare_1_2_3_official_90s_junglednb/

### TODO
- Add various modes
    - Press key 6 to cycle
    - Neopixel LED should indicate mode
- [X] Add SD card support to get more samples
    - Flash LEDs to show error if SD card is not present
- [X] Turn self on/off by driving EN diode-or'd with button
- Cap volume at minimum rather than scale to zero
- Read battery with external resistor divider