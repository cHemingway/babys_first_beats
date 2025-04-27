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
    {"pin": board.EXTERNAL_BUTTON, "type":"loop", "filename": "Fat Upright 2 (JW3)_mono22k.wav"},
    {"pin": board.D5, "type":"sample", "filename": "Kick 06 (JW2)_mono22k.wav"},
    {"pin": board.D6, "type":"sample", "filename": "Snare 39 (JW2)_mono22k.wav"},
    {"pin": board.D9, "type":"sample", "filename": "Snare 09 (JW2)_mono22k.wav"}
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
mixer = audiomixer.Mixer(voice_count=2, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
mixer.voice[0].level = 0.25   # Sample
mixer.voice[1].level = 0.5    # Loop
audio.play(mixer)

# External power pin
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT
external_power.value = True
end_time = time.monotonic_ns()
print(f"Setup time: {(end_time - start_time)*1E-6:.3f} ms")
print(f"Entering main loop")

# Setup done
pixel.fill((0x00,0x00,0x00))


current_loop = None
current_sample = None
last_played_time = time.monotonic()


def currently_playing():
    ''' Check if any sound is currently playing '''
    for voice in mixer.voice:
        if voice.playing:
            return True
    return False


while True:
    # Check for button presses
    for pin_def in PIN_DEFINITIONS:
        pin_def["button"].update()
        if pin_def["button"].pressed:
            start_time = time.monotonic_ns()

            # Check if the button is a loop or sample
            if pin_def["type"] == "loop":
                # If the button is a loop, stop any currently playing loop
                if mixer.voice[1].playing:
                    mixer.voice[1].stop()
                # If we were previously playing this loop, then don't play it again
                if current_loop and current_loop["filename"] == pin_def["filename"]:
                    print(f"Already playing {pin_def['filename']}")
                    current_loop = None
                    continue
                # Load the new sound
                wave_file = open(pin_def["filename"], "rb")
                pin_def["wave"] = audiocore.WaveFile(wave_file)
                # Start the sound
                mixer.voice[1].play(pin_def["wave"], loop=True)
                current_loop = pin_def
                last_played_time = time.monotonic()
            elif pin_def["type"] == "sample":
                # If the button is a sample, stop any currently playing sound
                if mixer.voice[0].playing:
                    mixer.voice[0].stop()
                # Load the new sound
                wave_file = open(pin_def["filename"], "rb")
                pin_def["wave"] = audiocore.WaveFile(wave_file)
                # Start the sound
                mixer.voice[0].play(pin_def["wave"])
                current_sample = pin_def
                last_played_time = time.monotonic()
                # Turn on the neopixel
                pixel.fill((0x00, 0xFF, 0x00))
            else:
                print(f"Unknown type {pin_def['type']} for {pin_def['filename']}")
                continue

            end_time = time.monotonic_ns()
            print(f"Latency: {(end_time - start_time)*1E-6:.3f} ms")

    
    # Wait for the sound to finish
    if current_sample and not mixer.voice[0].playing:
        # Turn off the neopixel
        pixel.fill((0x00, 0x00, 0x00))
        current_sample = None

    # If its been 10 seconds since the last sound was played, go to sleep
    if not currently_playing() and time.monotonic() - last_played_time > 10:
        alarms = setup_button_alarms()
        print("Going to sleep")
        # Turn off external power pin which deactivates the audio amplifier
        external_power.value = False
        # Go to sleep
        alarm.exit_and_deep_sleep_until_alarms(*alarms)
        

    time.sleep(0.005)
