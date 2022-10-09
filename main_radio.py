import signal
import RPi.GPIO as GPIO
import subprocess
import threading
import os

import Station
from MyDisplays import SqauareDisplay

# SystemD service description located here: /lib/systemd/system/my_radio.service

print("""buttons.py - Detect which button has been pressed

This example should demonstrate how to:
1. set up RPi.GPIO to read buttons,
2. determine which button has been pressed

Press Ctrl+C to exit!

""")

station_list = Station.Stations().Station_list
display = SqauareDisplay()


isPlaying = None 
isMuted = False
SET_VOLUME = 100

# The buttons on Pirate Audio are connected to pins 5, 6, 16 and 24
# Boards prior to 23 January 2020 used 5, 6, 16 and 20 
# try changing 24 to 20 if your Y button doesn't work.
BUTTONS = [5, 6, 16, 24]

# These correspond to buttons A, B, X and Y respectively
LABELS = ['A', 'B', 'X', 'Y']

# Set up RPi.GPIO with the "BCM" numbering scheme
GPIO.setmode(GPIO.BCM)

# Buttons connect to ground when pressed, so we should set them up
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def play(station:Station._Station, display:SqauareDisplay):
    global isPlaying
    print("\t### Trying to play...")
    if isPlaying:
        stop()
    display.show(station.path_icon)
    display.show_composite(station.path_icon, station_list['bbc_4'].path_icon,\
         station_list['bbc_6'].path_icon, 'pause', 'mute')
    os.system(f"mpv {station.path_m3u8} --no-video --input-ipc-server=/tmp/mpvsocket --volume={SET_VOLUME} &")
    isPlaying=True
    print("\t### Should now be playing...")
    
def stop():
    os.system('echo "stop" | socat - /tmp/mpvsocket')

def pause():
    global isPlaying
    if isPlaying==True:
        print('Pausing...')
        os.system('echo \'{ "command": ["set_property", "pause", true] }\' | socat - /tmp/mpvsocket')
        isPlaying=False
    elif isPlaying==False:
        print('Resuming...')
        os.system('echo \'{ "command": ["set_property", "pause", false] }\' | socat - /tmp/mpvsocket')
        isPlaying=True
    else:
        print("Neither playing nor paused")

def mute():
    global isMuted
    if isMuted==True:
        print('UnMuting...')
        os.system(f'echo \'{{ "command": ["set_property", "volume", "{SET_VOLUME}"] }}\' | socat - /tmp/mpvsocket')
        isMuted=False
    elif isMuted==False:
        print('Resuming...')
        os.system('echo \'{ "command": ["set_property", "volume", "0"] }\' | socat - /tmp/mpvsocket')
        isMuted=True
    else:
        print("Neither playing nor paused")

# "handle_button" will be called every time a button is pressed
# It receives one argument: the associated input pin.
def handle_button(pin):
    global isPlaying
    label = LABELS[BUTTONS.index(pin)]
    print("Button press detected on pin: {} label: {}".format(pin, label))
    
    if label == 'A':            
            play(station_list['bbc_4'], display)
            
    if label == 'X':            
            play(station_list['bbc_6'], display)            
    
    if label == 'Y':           
            mute()          
            
    elif label == 'B':
        pause()

        

# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=200)


# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
