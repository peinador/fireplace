#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd home/pi/fireplace/fireplace
export TERM=xterm
sleep 40
sudo python main.py
cd /
