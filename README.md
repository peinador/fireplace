# fireplace

Fireplace is a Python package to run a fireplace animation in a raspberry Pi Zero W2.
It displays flame animations on a 8x8 ws2812 LED (neopixel) display.
It also sends audio output to a speaker connected to the pi (I2S encoding).
Additionally, a rotary encoder provies control over the intensity of the LEDs and speaker volume.

## Installation
To install the package run:
```
pip install -e .
```
Before running the animations two things need to be done:
1. Add audio files (MP3 or WAV) in `data/fireplace_mp3/`. A collection of free fireplace sounds can be found [here](https://www.freetousesounds.com/free-fireplace-sound-effects/).
2. Generate the noise files by running `python fireplace/lights/generate_noise_files`. This creates a series of numpy files in `data/perlin_noise`.

## Use
To run the main animation file run:
```
sudo python fireplace/main.py
```

The launcher file launcher.sh can be used to setup a crontab automatic execution upon booting. 
This can be done by opening crontab
```
crontab -e
```
and adding the following line
```
@reboot sh /home/pi/fireplace/launcher.sh >/home/pi/logs/cronlog 2>&1
```
changing the directories accordingly. Make sure that the logs folder exists.

## Development
To help during developement I wrote `send_files.sh`, which sends the contents of the package to the raspberry pi (except for the `.git` directory) over the ssh connection.
This avoids having to push and pull for every change.

To copy the code to the raspberry pi using ssh use:
```bash
source send_files.sh
```

## Wiring
The wiring is represented in the following diagram:
![Wiring diagram for the project](docs/board_design.jpg)

## References 
- [MAX98357A documentation](https://web.archive.org/web/20240106093728/https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp)
- [Adafruit NeoPixels on Raspberry Pi](https://web.archive.org/web/20240215090728/https://learn.adafruit.com/neopixels-on-raspberry-pi/overview)
- [Rotary encoders tutorial](https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-rotary-encoder)
