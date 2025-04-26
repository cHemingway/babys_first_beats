import alarm
import alarm.pin
import audiocore
import audiobusio
import audiomixer
import board
import time

from digitalio import DigitalInOut, Direction, Pull

import neopixel
from adafruit_debouncer import Button

print("Start")
start_time = time.monotonic_ns()

# Table of button pins and audio files
PIN_DEFINITIONS = [
    {"pin": board.EXTERNAL_BUTTON, "filename": "DJ_mono22k.wav"},
    {"pin": board.D5, "filename": "one_mono22k.wav"},
    {"pin": board.D6, "filename": "two_mono22k.wav"},
    {"pin": board.D9, "filename": "three_mono22k.wav"}
]


def setup_buttons():
    ''' Set up the buttons with pull-up resistors and debouncing '''
    for pin_def in PIN_DEFINITIONS:
        digital= DigitalInOut(pin_def["pin"])
        digital.direction = Direction.INPUT
        digital.pull = Pull.UP
        pin_def["digital"] = digital
        pin_def["button"] = Button(digital, interval=0.01)
setup_buttons()

def setup_button_alarms() -> list:
    ''' Set up alarms for each button pin so that they can wake the board from sleep '''
    alarms = []
    for pin_def in PIN_DEFINITIONS:
        # Disconnect the pin from the DigitalInOut object
        pin_def["digital"].deinit()
        # Set up the pin as a PinAlarm
        pin_alarm = alarm.pin.PinAlarm(pin_def["pin"], value=False, pull=True)
        alarms.append(pin_alarm)
    return alarms

# Setup neopixel
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.1
pixel.fill((0xFF,0x00,0x00))

# Setup audio mixer
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
mixer.voice[0].level = 0.25

# External power pin
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT
external_power.value = True
end_time = time.monotonic_ns()
print(f"Setup time: {(end_time - start_time)*1E-6:.3f} ms")
print(f"Entering main loop")

# Setup done
pixel.fill((0x00,0x00,0x00))


current_button = None
last_played_time = time.monotonic()

while True:
    # Check for button presses
    for pin_def in PIN_DEFINITIONS:
        pin_def["button"].update()
        if pin_def["button"].pressed:
            start_time = time.monotonic_ns()
            current_button = pin_def
            # Stop any currently playing sound
            if mixer.voice[0].playing:
                mixer.voice[0].stop()
            # Load the new sound
            wave_file = open(pin_def["filename"], "rb")
            pin_def["wave"] = audiocore.WaveFile(wave_file)
            # Start the sound
            audio.play(mixer)
            mixer.voice[0].play(pin_def["wave"])
            print(f"Playing {pin_def['filename']}")
            last_played_time = time.monotonic()
            # Turn on the neopixel
            pixel.fill((0x00, 0xFF, 0x00))
            end_time = time.monotonic_ns()
            print(f"Latency: {(end_time - start_time)*1E-6:.3f} ms")

    
    # Wait for the sound to finish
    if current_button and not mixer.voice[0].playing:
        print(f"Playback finished for {current_button['filename']}")
        # Turn off the neopixel
        pixel.fill((0x00, 0x00, 0x00))
        current_button = None

    # If its been 5 seconds since the last sound was played, go to sleep
    if current_button is None and time.monotonic() - last_played_time > 5:
        alarms = setup_button_alarms()
        print("Going to sleep")
        # Turn off external power pin which deactivates the audio amplifier
        external_power.value = False
        # Go to sleep
        alarm.exit_and_deep_sleep_until_alarms(*alarms)
        

    time.sleep(0.005)
