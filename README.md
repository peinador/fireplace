# fireplace

Fireplace is a Python package to run a fireplace animation in a raspberry Pi Zero W2.
It displays flame animations on a 8x8 ws2812 LED (neopixel) display.
It also sends audio output to a speaker connected to the pi (I2S encoding).
Additionally, a rotary encoder provies control over the intensity of the LEDs and speaker volume.

![GIF showing the end result](docs/demo_gif.gif)
## Installation
To install the package run:
```
pip install -e .
```
Before running the animations two things need to be done:
1. Add audio files (MP3 or WAV) in `data/fireplace_mp3/`. You might need to create the directory if it does not exist. A collection of free fireplace sounds can be found [here](https://www.freetousesounds.com/free-fireplace-sound-effects/).
2. Generate the noise image files by running `python fireplace/lights/generate_noise_files`. This creates a series of numpy files in `data/perlin_noise`.
3. Make sure that the audio output is configured as I2S; following the instructions in reference [1].
4. Raspberry Pi specific installs:
    ```bash
    # from reference [2] below
    # libraries to control neopixels
    sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
    sudo python3 -m pip install --force-reinstall adafruit-blinka
    ```
    and
    ```bash
    # from reference [3] below
    # library to read GPIO pins
    sudo apt-get update
    sudo apt-get install python3-rpi.gpio
    ```

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
changing the directories accordingly. Make sure that the logs direcory exists by doing `mkdir logs` where appropriate.

## Development
To help during developement I wrote `send_files.sh`, which sends the contents of the package to the raspberry pi (except for the `.git` directory) over the ssh connection.
This avoids having to push and pull for every change.

To copy the code to the raspberry pi using ssh use:
```bash
source send_files.sh
```
## Component List
- Rasperry Pi Zero W2 (+32GB microSD card)
- MAX98357A I2S 3W amplifier
- 3W 4 $\Omega$ speaker
- 20 mm Rotary encoder (without breakout board and resistors)
- 5V to 3.3V 4-way bidirectional level shifter 
- 8x8 WS2812 LED (Neopixel) matrix
- On-On miniature Toggle Switch
- USB-C Power connector mount
- 5cm x 7cm perforated PCB
- 159XXSSBK ABS enclosure 121 x 94 x 34
- Wire, block sockets, header sockets, soldering supplies.
- white card and wrapping paper used as light diffuser
## Wiring
The wiring is represented in the following diagram:
![Wiring diagram for the project](docs/board_design.jpg)

## References 
[1] [MAX98357A documentation](https://web.archive.org/web/20240106093728/https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp)

[2] [Adafruit NeoPixels on Raspberry Pi](https://web.archive.org/web/20240215090728/https://learn.adafruit.com/neopixels-on-raspberry-pi/overview)

[3] [Rotary encoders tutorial](https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-rotary-encoder)
