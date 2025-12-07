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

### Step 6: Test

Test that everything works:

```bash
# Test with direct execution (runs for 1 minute)
sudo .venv/bin/python fireplace/main.py --duration 1
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

There are two ways to run the fireplace:

### Option 1: Direct execution

Run the fireplace directly from the command line:

```bash
cd ~/fireplace
source .venv/bin/activate

# Run for 60 minutes (default) with 10 min fade-out
sudo python fireplace/main.py

# Run for a specific duration
sudo python fireplace/main.py --duration 30

# Custom fade-out duration (gradually decrease volume/brightness)
sudo python fireplace/main.py --duration 60 --fade-out 15

# Disable fade-out
sudo python fireplace/main.py --duration 30 --fade-out 0
```

> **Note:** `sudo` is required for NeoPixel DMA access to `/dev/mem`.

### Option 2: API server (recommended)

Run the API server to control the fireplace remotely from your local network:

```bash
cd ~/fireplace
source .venv/bin/activate
sudo python fireplace/api.py
```

The server runs on port 8000 by default.

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start` | Start the fireplace (or update duration if running) |
| POST | `/stop` | Stop the fireplace |
| POST | `/volume` | Set volume (0-100) |
| GET | `/status` | Get current status (running, remaining time, volume) |
| GET | `/health` | Health check |

#### Examples

```bash
# Start the fireplace for 30 minutes with 10 min fade-out
curl -X POST http://<pi-ip>:8000/start \
  -H "Content-Type: application/json" \
  -d '{"duration_minutes": 30, "fade_out_minutes": 10}'

# Update duration while running (resets timer)
curl -X POST http://<pi-ip>:8000/start \
  -d '{"duration_minutes": 60}'

# Set volume to 50%
curl -X POST http://<pi-ip>:8000/volume \
  -H "Content-Type: application/json" \
  -d '{"volume": 50}'

# Check status
curl http://<pi-ip>:8000/status
# Response: {"running": true, "remaining_seconds": 1800, "volume": 50}

# Stop the fireplace
curl -X POST http://<pi-ip>:8000/stop
```

### Auto-start on boot

To start the API server automatically when the Pi boots, run the install script:

```bash
chmod +x install_service.sh
./install_service.sh

# Start the service now
sudo systemctl start fireplace
```

After enabling, the API server will start automatically on boot and be available at `http://<pi-ip>:8000`.

**Useful commands:**

```bash
sudo systemctl status fireplace   # Check status
sudo systemctl restart fireplace  # Restart after code changes
sudo systemctl stop fireplace     # Stop the service
sudo journalctl -u fireplace -f   # View logs
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

For permanent configuration, edit `fireplace.service` and uncomment the `Environment=ALSA_DEVICE` line, then run `sudo systemctl daemon-reload && sudo systemctl restart fireplace`.

### Volume

If audio is too quiet, check the GAIN pin on the MAX98357A:
- Connected to GND: 3dB (quietest)
- Floating/unconnected: 9dB (default)
- Connected to VIN: 15dB (loudest)

### Read-only filesystem (recommended)

To protect the SD card from corruption when power is cut unexpectedly, enable the read-only overlay filesystem:

```bash
sudo raspi-config
# -> Performance Options -> Overlay File System -> Enable
# -> Reboot when prompted
```

This mounts the SD card as read-only and uses RAM for any writes. The fireplace works normally since it doesn't need to write to disk during operation.

**To make changes (update code, install packages):**

```bash
# 1. Disable overlay
sudo raspi-config
# -> Performance Options -> Overlay File System -> Disable
# -> Reboot

# 2. Make your changes
cd ~/fireplace
git pull
pip install -e .

# 3. Re-enable overlay
sudo raspi-config
# -> Performance Options -> Overlay File System -> Enable
# -> Reboot
```

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

### API server not accessible after boot

- Check logs: `sudo journalctl -u fireplace -n 50`
- Ensure the Pi has network connectivity
- Verify the server started: `curl http://localhost:8000/health`
- Check service status: `sudo systemctl status fireplace`

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
