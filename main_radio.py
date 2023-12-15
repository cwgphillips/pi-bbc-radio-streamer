import signal
from gpiozero import LED, Button
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

print("""main_radio.py - Firing up the internet radio!

Press Ctrl+C to exit!

""")

SET_VOLUME = 100
LONG_PRESS = 3

LOCAL_CONFIG_FILE_NAME = "local_config.json"

ONKYO_DEVICE_ID = "0009B0E4415A"

# The buttons on Pirate Audio are connected to pins 5, 6, 16 and 24
# Boards prior to 23 January 2020 used 5, 6, 16 and 20
# try changing 24 to 20 if your Y button doesn't work.
BUTTONS_AND_LABELS = {"A":5, "B":6, "X":16, "Y":24}
BUTTONS = list(BUTTONS_AND_LABELS.values())

# These correspond to buttons A, B, X and Y respectively
LABELS = list(BUTTONS_AND_LABELS.keys())

boot_up = True
is_playing = None
is_muted = False

button_start_times = {"5":None, "6":None, "16":None, "24":None}
button_end_times = {"5":None, "6":None, "16":None, "24":None}
button_press_durations = {"5":None, "6":None, "16":None, "24":None}

local_config = {'last_played': ""}

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
    try:
        onkyo.try_turn_off(onkyo_device_ip_address)
    except:
        pass


def try_load_local_config():
    global local_config
    if os.path.exists(LOCAL_CONFIG_FILE_NAME):
        with open(LOCAL_CONFIG_FILE_NAME) as json_file:
            local_config = json.load(json_file)


def play(station:Station._Station, display:SqauareDisplay):
    global is_playing
    global boot_up
    stopOK=stop()
    if stopOK==0 or boot_up:
        boot_up = False
        print("\t### Trying to play...")
        display.show_composite((station.path_icon, station.name), \
            (station_list['bbc_4'].path_icon, 'bbc_4'), \
                (station_list['bbc_6'].path_icon, 'bbc_6'), \
                    ('pause', 'pause'), ('mute', 'mute'))

        os.system(f"mpv {station.path_m3u8} --no-video --input-ipc-server=/tmp/mpvsocket --volume={SET_VOLUME} &")
        is_playing=True
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
    global is_playing
    if is_playing==True:
        print('Pausing...')
        os.system('echo \'{ "command": ["set_property", "pause", true] }\' | socat - /tmp/mpvsocket')
        is_playing=False
    elif is_playing==False:
        print('Resuming...')
        os.system('echo \'{ "command": ["set_property", "pause", false] }\' | socat - /tmp/mpvsocket')
        is_playing=True
    else:
        print("Neither playing nor paused")


def mute():
    global is_muted
    if is_muted==True:
        print('UnMuting...')
        os.system(f'echo \'{{ "command": ["set_property", "volume", "{SET_VOLUME}"] }}\' | socat - /tmp/mpvsocket')
        is_muted=False
    elif is_muted==False:
        print('Resuming...')
        os.system('echo \'{ "command": ["set_property", "volume", "0"] }\' | socat - /tmp/mpvsocket')
        is_muted=True
    else:
        print("Neither playing nor paused")


def pressed(btn):
    global button_start_time
    # print(f"button {btn.pin.number} was pressed")
    button_start_times[str(btn.pin.number)] = time.time()
    

def released(btn):
    global button_end_times, button_press_durations
    global is_playing

    pin = btn.pin.number

    button_end_times[str(pin)] = time.time()
    elapsed = button_end_times[str(pin)] - button_start_times[str(pin)]
    button_press_durations[str(pin)] = elapsed
       
    label = LABELS[BUTTONS.index(pin)]
    print(f"Button {pin} (label: {label}) was released after {elapsed} seconds.")

    if label == 'A':
        if elapsed:
            if elapsed < LONG_PRESS:
                play(station_list['bbc_4'], display)

    if label == 'X':
        if elapsed:
            if elapsed < LONG_PRESS:
                play(station_list['bbc_6'], display)

    if label == 'Y':
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


station_list = Station.Stations().Station_list
display = SqauareDisplay()
display.show('blank')
display.show_composite('blank', \
    (station_list['bbc_4'].path_icon, 'bbc_4'), \
        (station_list['bbc_6'].path_icon, 'bbc_6'), \
            ('pause', 'pause'), ('mute', 'mute'))


# Buttons connect to ground when pressed, so they should be set
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
for pin in BUTTONS:
    b = Button(pin, bounce_time=0.05)
    # b.when_pressed = handle_button
    b.when_pressed = pressed
    b.when_released = released


# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
try:
    # thread_onkyo = Thread(target=initialise_onkyo)
    # thread_onkyo.start()
    try_load_local_config()
    try_playing_last_played()        
    signal.pause()    
except KeyboardInterrupt:
    display.show('blank')
    print("\nKeyboardInterrupt -- quitting")
    try_turn_off_onkyo()
    pass
