#!/bin/sh
# launcher.sh
# Start the fireplace simulation on boot

cd /home/pi/fireplace
export TERM=xterm

# ALSA device for audio output (default: softvol from Adafruit I2S installer)
# Uncomment and modify if your device is different:
# export ALSA_DEVICE="softvol"

# Wait for system to fully boot (audio, GPIO, etc.)
sleep 40

# Run with sudo (required for NeoPixel DMA access)
sudo -E .venv/bin/python fireplace/main.py
