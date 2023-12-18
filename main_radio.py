import signal
from gpiozero import Button
import os
import time
import json

import Station
from MyDisplays import SqauareDisplay
import onkyo

# SystemD service description located here: /lib/systemd/system/my_radio.service

print("""main_radio.py - Firing up the internet radio!

SystemD service description located here: /lib/systemd/system/my_radio.service

Press Ctrl+C to exit!

""")

SET_VOLUME = 100
LONG_PRESS = 2

LOCAL_CONFIG_FILE_NAME = "local_config.json"

ONKYO_DEVICE_ID = "0009B0E4415A"

DEFAULT_STATION_INDEX_A = 3
DEFAULT_STATION_INDEX_X = 4

# The buttons on Pirate Audio are connected to pins 5, 6, 16 and 24
# Boards prior to 23 January 2020 used 5, 6, 16 and 20
# try changing 24 to 20 if your Y button doesn't work.
BUTTONS_AND_LABELS = {"A":5, "B":6, "X":16, "Y":24}
BUTTONS = list(BUTTONS_AND_LABELS.values())

# These correspond to buttons A, B, X and Y respectively
LABELS = list(BUTTONS_AND_LABELS.keys())

Button.was_held = False

boot_up = True
is_playing = None
is_stopped = True
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
    global is_playing, is_stopped
    global boot_up
    global display_areas_map

    stopOK=stop()

    if stopOK==0 or boot_up:
        boot_up = False
        print("\t### Trying to play...")

        display_areas_map["Main"] = stations.station_for_display(station.name)
        display_areas_map["B"] = "pause"
        display.show_composite(*display_areas_map.values())

        os.system(f"mpv {station.path_m3u8} --no-video --input-ipc-server=/tmp/mpvsocket --volume={SET_VOLUME} &")
        is_playing = True
        is_stopped = False
        update_last_played(station.name)
        print(f"\t### Should now be playing {station.name}...")


def stop():
    global display_areas_map, is_stopped
    sysOut = os.system('echo "stop" | socat - /tmp/mpvsocket && rm /tmp/mpvsocket')
    if sysOut == 0:
        display_areas_map["Main"] = "blank"
        display_areas_map["B"] = "blank"
        display.show_composite(*display_areas_map.values())
        is_stopped = True
    return sysOut


def pause():
    global is_playing
    if is_playing is True:
        print('Pausing...')
        os.system('echo \'{ "command": ["set_property", "pause", true] }\' | socat - /tmp/mpvsocket')
        is_playing = False
        display_areas_map["B"] = "play"
    elif is_playing is False:
        print('Resuming...')
        os.system('echo \'{ "command": ["set_property", "pause", false] }\' | socat - /tmp/mpvsocket')
        display_areas_map["B"] = "pause"
        is_playing = True
    else:
        print("Neither playing nor paused")
    display.show_composite(*display_areas_map.values())


def mute():
    global is_muted
    if is_muted is True:
        print('UnMuting...')
        os.system(f'echo \'{{ "command": ["set_property", "volume", "{SET_VOLUME}"] }}\' | socat - /tmp/mpvsocket')
        display_areas_map["Y"] = "mute"
        is_muted=False
    elif is_muted is False:
        print('Muting...')
        os.system('echo \'{ "command": ["set_property", "volume", "0"] }\' | socat - /tmp/mpvsocket')
        display_areas_map["Y"] = "unmute"
        is_muted=True
    else:
        print("Neither playing nor paused")
    display.show_composite(*display_areas_map.values())


def held(btn):
    btn.was_held = True
    pin = btn.pin.number
    label = LABELS[BUTTONS.index(pin)]
    print(f"\t### Button {pin} (label: {label}) was held")

    if label == "A" or label == "X":
        cycle_through_displayed_station(label)


def cycle_through_displayed_station(label):
    global display_areas_map

    next_station_name = get_next_station_name(label)
    display_areas_map[label] = stations.station_for_display(next_station_name)
    display.show_composite(*display_areas_map.values())


def get_next_station_name(label):
    current_station_name = display_areas_map[label][1]
    next_station_index = station_names.index(current_station_name) + 1

    if next_station_index >= len(station_names):
        next_station_index = 0

    next_station_name = station_names[next_station_index]

    return next_station_name


def pressed(btn):
    global button_start_time

    button_start_times[str(btn.pin.number)] = time.time()
    btn.was_held = False


# https://github.com/gpiozero/gpiozero/issues/685#issuecomment-454201563
def released(btn):
    pin = btn.pin.number

    if btn.was_held:
        print(f"\t### Button {pin} was held so skipping...")
        return

    global button_end_times, button_press_durations
    global is_playing

    button_end_times[str(pin)] = time.time()
    elapsed = button_end_times[str(pin)] - button_start_times[str(pin)]
    button_press_durations[str(pin)] = elapsed
       
    label = LABELS[BUTTONS.index(pin)]
    print(f"\t### Button {pin} (label: {label}) was released after {elapsed} seconds.")


    if label == "A" or label == "X":
        if elapsed:
            if elapsed < LONG_PRESS:
                station_name = display_areas_map[label][1]
                print(f"\t### station_name {station_name}")
                play(station_dictionary[station_name], display)

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
        play(station_dictionary[last_played], display)


stations = Station.Stations()
station_dictionary = stations.station_dictionary
station_names = stations.station_names()

display_areas_map = {
    "Main": "blank",
    "A": stations.station_for_display(station_names[DEFAULT_STATION_INDEX_A]),
    "X": stations.station_for_display(station_names[DEFAULT_STATION_INDEX_X]),
    "B": "pause",
    "Y": "mute"
}

display = SqauareDisplay()
display.show('blank')
display.show_composite(*display_areas_map.values())

# Buttons connect to ground when pressed, so they should be set
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
for pin in BUTTONS:
    b = Button(pin, bounce_time=0.05, hold_time=LONG_PRESS+2, hold_repeat=True)
    b.when_pressed = pressed
    b.when_released = released
    b.when_held = held

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
