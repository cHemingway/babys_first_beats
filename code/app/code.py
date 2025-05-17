import audiocore
import audiobusio
import audiomixer
import board
import time
import keypad

from digitalio import DigitalInOut, Direction
import analogio

import neopixel

import mount_sd

MAX_VOLUME = 0.25  # Maximum volume level, adjust as needed


print("Start")
start_time = time.monotonic_ns()

# Setup keypad
keypad = keypad.KeyMatrix(
    row_pins = [board.D5, board.D6, board.D9],
    column_pins = [board.D10, board.D11, board.D12],
)


# Volume control
volume_dial = analogio.AnalogIn(board.A0)
def get_volume():
    # Convert the raw value to a volume level between 0 and 1
    scale = volume_dial.value / 65535
    # Scale logarithmically to get a more natural volume curve
    volume = scale ** 1.4
    # Scale to maximum volume range
    volume = volume * MAX_VOLUME
    # Ensure volume is at least 0.025 to avoid silence
    volume = max(volume, 0.025)  
    return volume


# Table of button pins and audio files
KEY_DEFINITIONS_PIRATE = [
    {"key": 7, "type":"loop", "filename":   "/sd/Diesel Not Petrol [-JqV1uJQaLU]_mono22k.wav"},
    {"key": 0, "type":"sample", "filename": "/sd/Worries Soundboy [2025-04-27 210147]_mono22k.wav"},
    {"key": 1, "type":"sample", "filename": "/sd/Killa Vox [2025-04-27 210139]_mono22k.wav"},
    {"key": 2, "type":"sample", "filename": "/sd/Ruling Bad Boy Tune [2025-04-27 210146]_mono22k.wav"},
    {"key": 3, "type":"sample", "filename": "/sd/Champion Badman [2025-04-27 210142]_mono22k.wav"},
    {"key": 4, "type":"sample", "filename": "/sd/bleep [2025-04-27 210136]_mono22k.wav"},
    {"key": 5, "type":"sample", "filename": "/sd/Air Horn Sound Effect [IpyingiCwV8]_mono22k.wav"}
]

KEY_DEFINITIONS_OLD_HIPHOP = [
    {"key": 7, "type":"loop", "filename":   "/sd/Fight The Power (Instrumental) - Public Enemy (Produced By The Bomb Squad)_mono22k.wav"},
    {"key": 0, "type":"sample", "filename": "/sd/Effect (50) [2025-04-27 210132]_mono22k.wav"},
    {"key": 1, "type":"sample", "filename": "/sd/Six Million Vox [2025-04-27 210144]_mono22k.wav"},
    {"key": 2, "type":"sample", "filename": "/sd/wu-tang_clan_-_c.r.e.a.m._(complete_acapella) [2025-04-27 201019]_mono22k.wav"},
    {"key": 3, "type":"sample", "filename": "/sd/Scratch 2 b [2025-04-27 205203]_mono22k.wav"},
    {"key": 4, "type":"sample", "filename": "/sd/Scratch_Kick [2025-04-27 210138]_mono22k.wav"},
    {"key": 5, "type":"sample", "filename": "/sd/wu-tang_clan_-_c.r.e.a.m._(complete_acapella) [2025-04-27 201019]_mono22k.wav"}
]

KEY_DEFINITIONS_TOTAL = [
    {"color":(0x80,00,0x80), "defs":KEY_DEFINITIONS_PIRATE},
    {"color":(0xFF,0xFF,0x00), "defs":KEY_DEFINITIONS_OLD_HIPHOP}
]

# Setup neopixel
pixel = neopixel.NeoPixel(board.EXTERNAL_NEOPIXELS, 2, pixel_order=neopixel.GRB)
pixel.brightness = 1
pixel.fill((0xFF,0x00,0x00))

# Setup audio mixer
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
mixer = audiomixer.Mixer(voice_count=2, 
                         buffer_size=2048,  # Increased over 1024 to avoid buffer underruns
                         sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True,)
volume = get_volume()
mixer.voice[0].level = volume   # Sample
mixer.voice[1].level = volume*0.5    # Loop
audio.play(mixer)

# Power off pin, connected to KILL external adafruit pushbutton power switch latch board 
# https://www.adafruit.com/product/1400
kill_power_pin = DigitalInOut(board.D13)
kill_power_pin.switch_to_output(value=False)

# External power pin
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT
external_power.value = True
end_time = time.monotonic_ns()

# Mount the SD card
print("Mounting SD card")
mount_sd.mount()

print(f"Setup time: {(end_time - start_time)*1E-6:.3f} ms")
print("Entering main loop")

# Setup done
pixel.fill((0x00,0x00,0x00))


# State variables
current_mode = KEY_DEFINITIONS_TOTAL[0]
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
    if event := keypad.events.get():
        if event.pressed:
            # Check if the button is a mode change
            if event.key_number == 6:
                # Change the mode
                current_mode = KEY_DEFINITIONS_TOTAL[1] if current_mode == KEY_DEFINITIONS_TOTAL[0] else KEY_DEFINITIONS_TOTAL[0]
                pixel.fill(current_mode["color"])
                # Stop any currently playing sound
                if current_sample:
                    mixer.voice[0].stop()
                    current_sample = None
                if current_loop:
                    mixer.voice[1].stop()
                    current_loop = None
                continue

            # Check if the button is a loop or sample
            for pin_def in current_mode["defs"]:
                if event.key_number == pin_def["key"]:
                    start_time = time.monotonic_ns()
                    # If the button is a loop, stop any currently playing loop
                    if pin_def["type"] == "loop":
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
                        pixel.fill((0xFF, 0x00, 0x00))
                    else:
                        print(f"Unknown type {pin_def['type']} for {pin_def['filename']}")
                    end_time = time.monotonic_ns()
                    print(f"Latency: {(end_time - start_time)*1E-6:.3f} ms")

    # Check if the volume dial has changed
    volume = get_volume()
    if volume != mixer.voice[0].level:
        mixer.voice[0].level = volume * 1
        mixer.voice[1].level = volume * 0.5
    
    # Wait for the sound to finish
    if current_sample and not mixer.voice[0].playing:
        # Turn off the neopixel
        pixel.fill((0x00, 0x00, 0x00))
        current_sample = None

    # Turn off if no sound has been played for 10 minutes
    if not currently_playing() and (time.monotonic() - last_played_time > 600):
            print("No sound played for 10 minutes, turning off")
            external_power.value = False
            time.sleep(0.5)
            kill_power_pin.value = True
            print("Should now be off")
            while True:
                time.sleep(1)

    # Sleep for a short time to avoid busy waiting
    time.sleep(0.02)