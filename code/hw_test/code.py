import alarm
import audiocore
import audiobusio
import audiomixer
import board
import busio
import time

from digitalio import DigitalInOut, Direction, Pull

import neopixel
import adafruit_lis3dh

print("Start")

# Turn on neopixel
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.1

pixel.fill((0xFF,0xA5,0))

# Turn on external neopixel
external_pixel = neopixel.NeoPixel(board.EXTERNAL_NEOPIXEL, 1)
external_pixel.brightness = 0.1
external_pixel.fill((0xFF,0xA5,0))

# Speak to accelerometer
i2c = board.I2C()  # uses board.SCL and board.SDA
accel_int1 = DigitalInOut(board.ACCELEROMETER_INTERRUPT)
accel = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=accel_int1)
accel.range = adafruit_lis3dh.RANGE_4_G


# Set tap detection to double taps.  The first parameter is a value:
#  - 0 = Disable tap detection.
#  - 1 = Detect single taps.
#  - 2 = Detect double taps.

# The second parameter is the threshold and a higher value means less sensitive
# tap detection.  Note the threshold should be set based on the range above:
#  - 2G = 40-80 threshold
#  - 4G = 20-40 threshold
#  - 8G = 10-20 threshold
#  - 16G = 5-10 threshold
accel.set_tap(1, 100)

# enable external power pin
# provides power to the external components
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT
external_power.value = True

print("Power On")

# i2s playback
wave_file = open("hypefunk - antonio - drumloop compressed_mono22k.wav", "rb")
wave = audiocore.WaveFile(wave_file)
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
audio.play(mixer)
mixer.voice[0].level = 0.1
mixer.voice[0].play(wave, loop=False)
print("Playing")

#Keep LED on if playing
external_pixel.fill((0x00,0x00,0xFF))


while mixer.voice[0].playing:
    time.sleep(0.1)
    if accel.tapped:
        pixel.fill((0xFF,0xFF,0xFF))
    else:
        pixel.fill((0x00,0x00,0xFF))


external_pixel.fill((0x00, 0xFF, 0x00))
print("Done")

