#!/bin/bash

# Copy current directory to Raspberry Pi over SSH
rsync -av --exclude='.git' ./ pi@raspberrypi:/home/pi/fireplace

echo "Directory copied successfully."
