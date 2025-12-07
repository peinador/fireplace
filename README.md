# Fireplace 🔥

Who doesn't like the soft flickering light and crackling sounds of a fireplace? The fire brigade and my landlord.

Fireplace is a Python package to run a fireplace animation in a Raspberry Pi Zero W.
It displays a flame animation on an 8x8 WS2812 LED (NeoPixel) display.
It also sends audio output to a speaker connected to the Pi (I2S encoding).
Additionally, a rotary encoder provides control over the intensity of the LEDs and speaker volume.

<img src="docs/demo_gif.gif" alt="GIF showing the end result" height="300"/>  <img src="docs/demo_gif_2.gif" alt="GIF showing the end result" height="300"/>

## Installation

### Prerequisites

- Raspberry Pi Zero W (or Zero W2) with Raspberry Pi OS (Bookworm or later)
- Hardware components connected (see [Wiring](#wiring) section)

### Step 1: Configure I2S Audio

Follow the [Adafruit MAX98357A I2S setup guide](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/raspberry-pi-usage) to configure I2S audio:

```bash
# Install required packages
sudo apt install -y wget python3-venv

# Create and activate virtual environment for the installer
python3 -m venv ~/i2s-installer --system-site-packages
source ~/i2s-installer/bin/activate

# Install Adafruit shell helper and run I2S installer
pip3 install adafruit-python-shell
wget https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/raw/main/i2samp.py
sudo -E env PATH=$PATH python3 i2samp.py

# Deactivate installer venv
deactivate
```

**Important:** You must reboot **twice** after running the installer:
1. First reboot enables the I2S hardware
2. Second reboot (after testing audio) enables volume control in alsamixer

After the second reboot, test audio:
```bash
speaker-test -c2 -t wav
```

### Step 2: Install system packages

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-numpy \
    python3-rpi-lgpio \
    mpg123
```

> **Note:** On Raspberry Pi OS Bookworm/Trixie, use `python3-rpi-lgpio` (not `python3-rpi.gpio`). The older library doesn't work with the new kernel GPIO subsystem.

### Step 3: Clone and set up the project

```bash
cd ~
git clone https://github.com/peinador/fireplace.git
cd fireplace

# Create venv with access to system packages (for numpy, GPIO)
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Install Adafruit libraries for NeoPixel control
pip install rpi_ws281x adafruit-circuitpython-neopixel adafruit-blinka

# Install the fireplace package
pip install -e .
```

### Step 4: Add audio files

Add MP3 or WAV audio files to `data/audio_files/`. Free fireplace sounds: [freetousesounds.com](https://www.freetousesounds.com/free-fireplace-sound-effects/)

```bash
mkdir -p data/audio_files
# Copy your audio files here
```

### Step 5: Generate noise files

Generate the Perlin noise files for the flame animation:

```bash
python fireplace/lights/generate_noise_files.py
```

### Step 6: Test audio

The script auto-detects your I2S audio device. Test that audio works:

```bash
# Test audio (the script will auto-detect the device)
sudo .venv/bin/python fireplace/main.py
```

If audio doesn't work, you can manually specify the device:

```bash
# List available audio devices
aplay -l

# Find your I2S device (not HDMI) and test it
sudo mpg123 -o alsa -a "plughw:CARD=<your_card_name>,DEV=0" data/audio_files/your_file.mp3

# Then set it for the script
export ALSA_DEVICE="plughw:CARD=<your_card_name>,DEV=0"
```

## Usage

Run the fireplace simulation:

```bash
cd ~/fireplace
source .venv/bin/activate
sudo python fireplace/main.py
```

> **Note:** `sudo` is required for NeoPixel DMA access to `/dev/mem`.

### Auto-start on boot

1. Create a logs directory:
   ```bash
   mkdir -p ~/logs
   ```

2. Add to crontab:
   ```bash
   crontab -e
   ```
   
   Add this line:
   ```
   @reboot sh /home/pi/fireplace/launcher.sh >/home/pi/logs/cronlog 2>&1
   ```

## Configuration

### Audio Device

The script **auto-detects** your I2S audio device by scanning for non-HDMI audio hardware.

If auto-detection doesn't work, set the `ALSA_DEVICE` environment variable:

```bash
# Find your device
aplay -l
# Look for the non-HDMI card, e.g., "card 1: sndrpigooglevoi"

# Set the device
export ALSA_DEVICE="plughw:CARD=sndrpigooglevoi,DEV=0"
sudo -E python fireplace/main.py
```

For permanent configuration, edit `launcher.sh` and uncomment the `ALSA_DEVICE` line.

### Volume

If audio is too quiet, check the GAIN pin on the MAX98357A:
- Connected to GND: 3dB (quietest)
- Floating/unconnected: 9dB (default)
- Connected to VIN: 15dB (loudest)

## Troubleshooting

### No audio output

1. Verify I2S is configured: `aplay -l` should show your I2S device
2. Test audio directly: `sudo mpg123 -o alsa -a softvol <file.mp3>`
3. Try different ALSA devices from `aplay -L`
4. Check that you rebooted **twice** after I2S installer

### Audio works from command line but not from script

- The script specifies the ALSA device explicitly
- Set `ALSA_DEVICE` environment variable to match your working device

### GPIO errors ("Failed to add edge detection")

- Use `python3-rpi-lgpio`, not `python3-rpi.gpio`
- Reboot after changing GPIO libraries

### LEDs not working / Permission denied

- Must run with `sudo` for NeoPixel DMA access
- Check wiring (data pin is GPIO 12)

### NeoPixels work but audio doesn't

- Audio must be configured for root user
- The Adafruit I2S installer configures `/etc/asound.conf` which works for all users

## Development

The [tests folder](/tests) includes scripts to independently test each component:
- `tests/leds_test.py` - Test LED matrix
- `tests/audio_test.py` - Test audio playback  
- `tests/rotary_test.py` - Test rotary encoder

The LED animation uses Perlin noise. The algorithm is explained in [this notebook](/docs/noise.ipynb).

### Syncing code to the Pi

```bash
# Update SSH credentials in send_files.sh first
source send_files.sh
```

## Hardware

### Component List

- Raspberry Pi Zero W or W2 (+32GB microSD card)
- MAX98357A I2S 3W amplifier
- 3W 4Ω speaker
- 20mm rotary encoder (without breakout board)
- 5V to 3.3V 4-way bidirectional level shifter
- 8x8 WS2812 LED (NeoPixel) matrix
- On-On miniature toggle switch
- USB-C power connector mount
- 5cm x 7cm perforated PCB
- 159XXSSBK ABS enclosure (121 x 94 x 34mm)
- Wire, sockets, headers, soldering supplies
- White card and wrapping paper (light diffuser)

### Wiring

![Wiring diagram for the project](docs/board_design.jpg)

| Colour | Description | GPIO |
|--------|-------------|------|
| Black | Ground | |
| Red | 5V | |
| Orange | 3.3V | |
| Light Green | LED data (3.3V side) | 12 |
| Lilac | LED data (5V side) | |
| Salmon | Rotary encoder CLK | 23 |
| Brown | Rotary encoder DT | 8 |
| Purple | I2S LRC (amplifier) | 19 |
| Blue | I2S BCLK (amplifier) | 18 |
| Dark Green | I2S DIN (amplifier) | 21 |

## References

1. [MAX98357A I2S Amplifier Setup](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/raspberry-pi-usage)
2. [Adafruit NeoPixels on Raspberry Pi](https://learn.adafruit.com/neopixels-on-raspberry-pi/overview)
3. [Rotary Encoder Tutorial](https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-rotary-encoder)
