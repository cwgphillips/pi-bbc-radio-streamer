import signal
from gpiozero import Button
import os
import time
import json
import subprocess

import paho.mqtt.client as paho

import Station
from MyDisplays import SqauareDisplay
import onkyo

# SystemD service description located here: /lib/systemd/system/my_radio.service

print("""main_radio.py - Firing up the internet radio!

SystemD service description located here: /lib/systemd/system/my_radio.service

Press Ctrl+C to exit!

""")

MQTT_ADDRESS = "192.168.1.137"

SET_VOLUME = 100
LONG_PRESS = 1

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
mpv_process = None
ignore_next_release = None
button_pressed_state = {"A": False, "B": False, "X": False, "Y": False} 

button_start_times = {"5":None, "6":None, "16":None, "24":None}
button_end_times = {"5":None, "6":None, "16":None, "24":None}
button_press_durations = {"5":None, "6":None, "16":None, "24":None}

local_config = {'last_played': ""}

global onkyo_device_ip_address
global client

def mqtt_message_handling(client, userdata, msg):
    global is_playing
    print(f"\t### MQTT Message: {msg.topic}: {msg.payload.decode()}")

    if "bbc" in msg:
        if "1" in msg:
            station_name = "bbc_1"
        if "2" in msg:
            station_name = "bbc_2"
        if "3" in msg:
            station_name = "bbc_3"
        if "4" in msg:
            station_name = "bbc_4"
        if "6" in msg:
            station_name = "bbc_6"
        
        print(f"\t### station_name {station_name}")
        play(station_dictionary[station_name], display)

    if "mute" in msg:
        print(f"...muting")
        mute()

    if "shutdown" in msg:
        print(f"t= ...shutting down")
        shutdown_now()

    if "pause" in msg:
        print(f"t= ...pause")
        pause()

    if "stop" in msg:
        print(f"t= ...stop")
        stop()


def initialise_mqtt():
    global client
    client = paho.Client()
    client.on_message = mqtt_message_handling

    if client.connect(MQTT_ADDRESS, 1883, 60) != 0:
        print("Couldn't connect to the mqtt broker")

    client.subscribe("test_topic")    
    

def initialise_onkyo():
    global onkyo_device_ip_address
    onkyo_devices = onkyo.try_get_devices()
    onkyo_device_ip_address = onkyo_devices[ONKYO_DEVICE_ID]
    try_turn_on_onkyo()


def try_turn_on_onkyo():
    global onkyo_device_ip_address
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
    global is_playing, is_stopped, boot_up, display_areas_map, mpv_process

    stop() # Clean up any existing state without checking for a return code

    boot_up = False
    print("\t### Trying to play...")

    display_areas_map["Main"] = stations.station_for_display(station.name)
    display_areas_map["B"] = "pause"
    display.show_composite(*display_areas_map.values())

    mpv_process = subprocess.Popen([
        "mpv",
        f"--demuxer-lavf-o=protocol_whitelist=[http,https,tcp,file]",
        station.path_m3u8,
        "--no-video",
        "--input-ipc-server=/tmp/mpvsocket",
        "--cache=yes",
        "--demuxer-max-bytes=10M",
        "--demuxer-max-back-bytes=5M",
        "--stream-buffer-size=2M",
        "--network-timeout=30",
        "--force-seekable=yes",
        f"--volume={SET_VOLUME}"
    ])
    
    is_playing = True
    is_stopped = False
    update_last_played(station.name)
    print(f"\t### Should now be playing {station.name}...")


def stop():
    global display_areas_map, is_stopped, mpv_process
    
    # Terminate the process cleanly if it exists
    if mpv_process and mpv_process.poll() is None:
        mpv_process.terminate()
        mpv_process.wait()

    # Clean up the socket file to prevent conflicts on the next run
    if os.path.exists('/tmp/mpvsocket'):
        os.remove('/tmp/mpvsocket')

    display_areas_map["Main"] = "blank"
    display_areas_map["B"] = "blank"
    display.show_composite(*display_areas_map.values())
    is_stopped = True
    
    return 0 # Always return success so play() doesn't get blocked


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


def rewind():
    global is_playing
    if is_playing:
        print('### Rewinding 10 seconds...')
        # Sends a relative seek command (-10 seconds) to the running mpv process
        os.system('echo \'{ "command": ["seek", -10] }\' | socat - /tmp/mpvsocket')


def fast_forward():
    global is_playing
    if is_playing:
        print('### Fast forwarding 10 seconds...')
        # Seeks forward 10 seconds (only works if you've already rewound)
        os.system('echo \'{ "command": ["seek", 10] }\' | socat - /tmp/mpvsocket')


def return_to_live():
    global is_playing
    if is_playing:
        print('### Returning to live stream...')
        # Seeks to 100% of the current buffer to catch up to live broadcast
        os.system('echo \'{ "command": ["seek", 100, "absolute-percent"] }\' | socat - /tmp/mpvsocket')


def held(btn):
    btn.was_held = True
    pin = btn.pin.number
    label = LABELS[BUTTONS.index(pin)]
    print(f"\t### Button {pin} (label: {label}) was held")

    if label == "A" or label == "X":
        cycle_through_displayed_station(label)
    elif label == "Y":
        shutdown_now()
    elif label == "B":
        stop()


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
    global button_start_times, button_pressed_state
    
    pin = btn.pin.number
    label = LABELS[BUTTONS.index(pin)]

    button_start_times[str(pin)] = time.time()
    button_pressed_state[label] = True # Logically mark it as pressed
    btn.was_held = False


# https://github.com/gpiozero/gpiozero/issues/685#issuecomment-454201563
def released(btn):
    pin = btn.pin.number
    label = LABELS[BUTTONS.index(pin)]

    if btn.was_held:
        print(f"\t### Button {pin} was held so skipping...")
        button_pressed_state[label] = False # Clear logical state
        return

    global button_end_times, button_press_durations
    global is_playing, ignore_next_release, button_pressed_state

    button_end_times[str(pin)] = time.time()
    elapsed = button_end_times[str(pin)] - button_start_times[str(pin)]
    button_press_durations[str(pin)] = elapsed
       
    button_pressed_state[label] = False # Mark as released locally
    print(f"\t### Button {pin} (label: {label}) was released after {elapsed} seconds.")

    # --- COMBO CHECK ---
    # 1. If this button was the second half of a combo, ignore it and clear the flag
    if ignore_next_release == label:
        ignore_next_release = None
        return

    # 2. Check for A+B (Rewind 10s)
    if (label == "A" and button_pressed_state["B"]) or \
       (label == "B" and button_pressed_state["A"]):
        rewind()
        ignore_next_release = "B" if label == "A" else "A"
        return 

    # 3. Check for X+Y (Fast Forward 10s)
    if (label == "X" and button_pressed_state["Y"]) or \
       (label == "Y" and button_pressed_state["X"]):
        fast_forward()
        ignore_next_release = "Y" if label == "X" else "X"
        return 

    # 4. Check for A+X (Return to Live)
    if (label == "A" and button_pressed_state["X"]) or \
       (label == "X" and button_pressed_state["A"]):
        return_to_live()
        ignore_next_release = "X" if label == "A" else "A"
        return 
    # -------------------

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
                shutdown_now()

    elif label == 'B':
        if elapsed:
            if elapsed < LONG_PRESS:
                pause()
            elif elapsed >= LONG_PRESS:
                stop()


def shutdown_now():
    print("\t### ...shutting down")
    display.show('blank')
    try_turn_off_onkyo()
    os.system("sudo shutdown -h now")


def update_last_played(station_name):
    local_config['last_played'] = station_name
    with open(LOCAL_CONFIG_FILE_NAME, 'w') as outfile:
        json.dump(local_config, outfile)


def try_playing_last_played():
    if local_config is not None:
        last_played = local_config['last_played']
        play(station_dictionary[last_played], display)


def watchdog_check():
    global mpv_process, is_playing, is_stopped
    
    # If the radio isn't paused or stopped, but the process died
    if is_playing and not is_stopped:
        if mpv_process is None or mpv_process.poll() is not None:
            print("\t### Watchdog: Stream died unexpectedly. Restarting in 3 seconds...")
            time.sleep(3)
            try_playing_last_played()


stations = Station.Stations()
station_dictionary = stations.station_dictionary
station_names = stations.station_names()

display_areas_map = {
    "Main": "blank",
    "A": stations.station_for_display(station_names[DEFAULT_STATION_INDEX_A]),
    "X": stations.station_for_display(station_names[DEFAULT_STATION_INDEX_X]),
    "B": "pause",
    "Y": "power"
}

display = SqauareDisplay()
display.show('blank')
display.show_composite(*display_areas_map.values())

# Buttons connect to ground when pressed, so they should be set
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
# Create a dictionary to store the button objects globally
hardware_buttons = {}

for pin in BUTTONS:
    b = Button(pin, bounce_time=0.05, hold_time=LONG_PRESS+0.5, hold_repeat=True)
    b.when_pressed = pressed
    b.when_released = released
    b.when_held = held
    
    # Save the button object using its label (A, B, X, Y) as the key
    label = LABELS[BUTTONS.index(pin)]
    hardware_buttons[label] = b

try:
    initialise_mqtt()
    try_load_local_config()
    try_playing_last_played()
    
    # Start the MQTT listener in the background instead of blocking forever
    client.loop_start() 
    
    # The new main loop that keeps Python alive and checks the stream
    while True:
        watchdog_check()
        time.sleep(1)

except KeyboardInterrupt:
    display.show('blank')
    print("\nKeyboardInterrupt -- quitting")
    try_turn_off_onkyo()
    if mpv_process:
        mpv_process.terminate() # Ensure mpv dies when you exit the script
