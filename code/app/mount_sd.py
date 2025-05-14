import board
import sdcardio
import storage

def mount():
    ''' Mount the SD card '''
    # Use the board's primary SPI bus
    spi = board.SPI()
    cs = board.D25  # Chip select pin for the SD card

    # Create the SD card object
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)

    # Mount the filesystem
    storage.mount(vfs, "/sd")