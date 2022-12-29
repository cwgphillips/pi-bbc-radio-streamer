import signal
import RPi.GPIO as GPIO
import subprocess
import threading
import os
import time
import json
from threading import Thread

import Station
from MyDisplays import SqauareDisplay
import onkyo

# SystemD service description located here: /lib/systemd/system/my_radio.service

print("""buttons.py - Detect which button has been pressed

This example should demonstrate how to:
1. set up RPi.GPIO to read buttons,
2. determine which button has been pressed

Press Ctrl+C to exit!

""")

station_list = Station.Stations().Station_list
display = SqauareDisplay()
display.show('blank')
display.show_composite('blank', \
    (station_list['bbc_4'].path_icon, 'bbc_4'), \
        (station_list['bbc_6'].path_icon, 'bbc_6'), \
            ('pause', 'pause'), ('mute', 'mute'))

isPlaying = None
isMuted = False
SET_VOLUME = 100
bootUp = True

# The buttons on Pirate Audio are connected to pins 5, 6, 16 and 24
# Boards prior to 23 January 2020 used 5, 6, 16 and 20
# try changing 24 to 20 if your Y button doesn't work.
BUTTONS_AND_LABELS = {"A":5, "B":6, "X":16, "Y":24}
BUTTONS = list(BUTTONS_AND_LABELS.values())

# These correspond to buttons A, B, X and Y respectively
LABELS = list(BUTTONS_AND_LABELS.keys())

LONG_PRESS = 3

# Set up RPi.GPIO with the "BCM" numbering scheme
GPIO.setmode(GPIO.BCM)

# Buttons connect to ground when pressed, so we should set them up
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

global buttonStartTimes
global buttonEndTimes
buttonStartTimes = {"A":None, "B":None, "X":None, "Y":None}
buttonEndTimes = {"A":None, "B":None, "X":None, "Y":None}

global local_config

local_config = {'last_played': ""}

LOCAL_CONFIG_FILE_NAME = "local_config.json"

ONKYO_DEVICE_ID = "0009B0E4415A"
global onkyo_device_ip_address

def initialise_onkyo():
    global onkyo_device_ip_address
    onkyo_devices = onkyo.try_get_devices()
    onkyo_device_ip_address = onkyo_devices[ONKYO_DEVICE_ID]
    try_turn_on_onkyo()

def try_turn_on_onkyo():
    print("\t### Turning on Onkyo")
    onkyo.try_turn_on(onkyo_device_ip_address)
    print("\t###Setting Onkyo volume")
    onkyo.try_set_volume(onkyo_device_ip_address, 12)
    print("\t### Setting Onkyo to 'aux1'")
    onkyo.try_set_source(onkyo_device_ip_address, 'aux1')

def try_turn_off_onkyo():
    onkyo.try_turn_off(onkyo_device_ip_address)

def try_load_local_config():
    global local_config
    if os.path.exists(LOCAL_CONFIG_FILE_NAME):
        with open(LOCAL_CONFIG_FILE_NAME) as json_file:
            local_config = json.load(json_file)


def play(station:Station._Station, display:SqauareDisplay):
    global isPlaying
    global bootUp
    stopOK=stop()
    if stopOK==0 or bootUp:
        bootUp = False
        print("\t### Trying to play...")
        display.show_composite((station.path_icon, station.name), \
            (station_list['bbc_4'].path_icon, 'bbc_4'), \
                (station_list['bbc_6'].path_icon, 'bbc_6'), \
                    ('pause', 'pause'), ('mute', 'mute'))

        os.system(f"mpv {station.path_m3u8} --no-video --input-ipc-server=/tmp/mpvsocket --volume={SET_VOLUME} &")
        isPlaying=True
        update_last_played(station.name)
        print(f"\t### Should now be playing {station.name}...")

def stop():
    sysOut = os.system('echo "stop" | socat - /tmp/mpvsocket')
    if sysOut == 0:
        display.show_composite('blank', \
            (station_list['bbc_4'].path_icon, 'bbc_4'), \
                (station_list['bbc_6'].path_icon, 'bbc_6'), \
                    ('pause', 'pause'), ('mute', 'mute'))
    return sysOut

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

def calc_curation(label):
    global buttonStartTimes
    global buttonEndTimes
    if GPIO.input(BUTTONS_AND_LABELS[label]) == 0:
        buttonStartTimes[label] = time.time()
        return None
    if GPIO.input(BUTTONS_AND_LABELS[label]) == 1:
        buttonEndTimes[label] = time.time()
        elapsed = buttonEndTimes[label] - buttonStartTimes[label]
        return elapsed

# "handle_button" will be called every time a button is pressed
# It receives one argument: the associated input pin.
def handle_button(pin):
    global isPlaying
    label = LABELS[BUTTONS.index(pin)]
    print("Button press detected on pin: {} label: {}".format(pin, label))

    if label == 'A':
            elapsed = calc_curation(label)
            if elapsed:
                if elapsed < LONG_PRESS:
                    play(station_list['bbc_4'], display)

    if label == 'X':
            elapsed = calc_curation(label)
            if elapsed:
                if elapsed < LONG_PRESS:
                    play(station_list['bbc_6'], display)

    if label == 'Y':
            elapsed = calc_curation(label)
            if elapsed:
                if elapsed < LONG_PRESS:
                    print(f"t={elapsed} ...muting")
                    mute()

                elif elapsed >= LONG_PRESS:
                    print(f"t={elapsed} ...shutting down")
                    display.show('blank')
                    try_turn_off_onkyo()
                    os.system("sudo shutdown -h now")

    elif label == 'B':
            elapsed = calc_curation(label)
            if elapsed:
                if elapsed < LONG_PRESS:
                    pause()
                elif elapsed >= LONG_PRESS:
                    stop()

def update_last_played(station_name):
    local_config['last_played'] = station_name
    with open(LOCAL_CONFIG_FILE_NAME, 'w') as outfile:
        json.dump(local_config, outfile)

def try_playing_last_played():
    if local_config is not None:
        last_played = local_config['last_played']   
        if last_played == 'bbc_4':
            play(station_list['bbc_4'], display)
        elif last_played == 'bbc_6':
            play(station_list['bbc_6'], display)

# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    # GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=200)
    GPIO.add_event_detect(pin, GPIO.BOTH, handle_button, bouncetime=50)


# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
try:
    thread_onkyo = Thread(target=initialise_onkyo)
    thread_onkyo.start()
    try_load_local_config()
    try_playing_last_played()        
    signal.pause()    
except KeyboardInterrupt:
    display.show('blank')
    print("\nKeyboardInterrupt -- quitting")
    try_turn_off_onkyo()
    pass
