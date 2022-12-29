# pi-bbc-radio-streamer
Stream radio with python, mpv, Raspberry Pi and Pirate-Audio hat.

We can't get good DAB signal in our kitchen so I wanted a simple radio with physical buttons I could stream radio. 

Streaming BBC radio seems to be harder than I thought but http://www.radiofeeds.co.uk/ provide loads of feeds you can use to stream many radio stations, including BBC.

This impliments a simple mpv player (https://mpv.io/) via a python app to stream radio (including BBC 6 music! 😊) from an _.m3u8_ file.

N.B. Tested on RPi Zero W and RPi Zero 2

# Set-up

## Install Pirate Audio bits
Install dependencies…
```
sudo apt update

sudo apt install python3-rpi.gpio python3-spidev python3-pip python3-pil python3-numpy
```

Then install the st7789 (screen) library:
```
sudo pip install st7789
```

## Settings for the screen and audio:
Add the following to /boot/config.txt, by doing `sudo nano /boot/config.txt` and copying in the following:
```
dtoverlay=hifiberry-dac
gpio=25=op,dh
```
Disable the onboard audio:
```
dtparam=audio=off
```

## Enable SPI
`sudo raspi-config
--> 3. Interface Options --> I4 SPI Enable/disable…
Yes`, to enable

## MPV
Install older version to avoid issues!
```
sudo apt install libmpv-dev=0.32.0-3
 
pip install python-mpv==0.5.2
```


## Clone my repo
Install git:
```
sudo apt-get install git
```

Clone repo:
```
git clone git@github.com:cwgphillips/pi-bbc-radio-streamer.git
```

Install additional packages:
For modifying svg images:
```
pip install cairosvg
```
For connecting to Onkyo:
```
pip install onkyo-eiscp
```


## Sound
Create a new audio config file in ~/.asoundrc by typing `nano ~/.asoundrc` and insterdint the following text:

	pcm.speakerbonnet {
	   type hw card 0
	}
	
	pcm.dmixer {
	   type dmix
	   ipc_key 1024
	   ipc_perm 0666
	   slave {
	     pcm "speakerbonnet"
	     period_time 0
	     period_size 1024
	     buffer_size 8192
	     rate 44100
	     channels 2
	   }
	}
	
	ctl.dmixer {
	    type hw card 0
	}
	
	pcm.softvol {
	    type softvol
	    slave.pcm "dmixer"
	    control.name "PCM"
	    control.card 0
	}
	
	ctl.softvol {
	    type hw card 0
	}
	
	pcm.!default {
	    type             plug
	    slave.pcm       "softvol"
	}

Save and exit (_ctrl+x, ctrl+y_)

Now reboot, then play some audio, then reboot again.
Use this to test the audio:
```
speaker-test -c2 --test=wav -w /usr/share/sounds/alsa/Front_Center.wav
```

Then you can type `alsamixer` to control the volume.

## Enable auto login
```
sudo raspi-config --> 1 System Options --> S5 Boot / Auto Login --> B2 Console Autologin
```

## Run from start up
Create a system file
```
sudo nano /usr/lib/systemd/system/my_radio.service
```
And add the following...

```
[Unit]
# Play my radio on boot
Description=my_radio
After=network.target

[Service]
Type=simple
PermissionsStartOnly=True
Environment="PYTHONUNBUFFERED=TRUE"
User=pi
Group=gpio
RuntimeDirectoryMode=0755
ExecStart=/bin/sh -c "cd /home/pi/repo/pi-bbc-radio-streamer && \
	python main_radio.py"
PIDFile=/home/pi/my_mpv_example/my_radio.pid
ExecStop=/usr/bin/pkill --signal SIGTERM --pidfile cd /home/pi/repo/pi-bbc-radio-streamer/my_radio.pid
WorkingDirectory=/home/pi/repo/pi-bbc-radio-streamer
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
```

Then enable and start the system file
```
sudo systemctl enable my_radio.service 
```
And then start it
```
sudo systemctl start my_radio.service
```


# Try reducing boot time 
To see how long boot took 
```
systemd-analyze
```

...and to see which service are ran and how much time they took:

```
systemd-analyze blame
```

## Bluetooth
I'm not using bluetooth so try disabling this service
Edit the config:
```
sudo nano /boot/config.txt
```
And then add to the end (to see more info read `/boot/overlays/README`)
```
# Disable Bluetooth
dtoverlay=disable-bt
```

Then disable the associated services running with it
```
sudo systemctl disable hciuart.service
sudo systemctl disable bluetooth.service
```




# Useful Referneces for Set-Up
Pirate-Audio HAT: https://github.com/pimoroni/pirate-audio

Screen on HAT: https://github.com/pimoroni/st7789-python

For Pin outs used: https://pinout.xyz/pinout/pirate_audio_headphone_amp 

Audio mixer: https://learn.adafruit.com/adafruit-speaker-bonnet-for-raspberry-pi?view=all#add-software-volume-control-2711421 

