#!/bin/bash

# Copy current directory to Raspberry Pi over SSH
rsync -av --exclude='.git' ./ pi@pizero:/home/pi/fireplace

echo "Directory copied successfully."
