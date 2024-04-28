# This Raspberry Pi code was developed by newbiely.com
# This Raspberry Pi code is made available for public use without any restriction
# For comprehensive instructions and wiring diagrams, please visit:
# https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-rotary-encoder

import time

import RPi.GPIO as GPIO

from fireplace.rotary_encoder.rotary import Counter, create_encoder_callback

CLK_PIN = 23
DT_PIN = 8

CLK_Last = GPIO.HIGH
dtLastState = GPIO.HIGH

if __name__ == "__main__":
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        counter = Counter(value=0.5, range=(0, 1))
        encoder_callback = create_encoder_callback(counter)
        GPIO.add_event_detect(CLK_PIN, GPIO.BOTH, callback=encoder_callback)
        while True:
            time.sleep(1)  # you can do other works here rather than an infinite loop
    except KeyboardInterrupt:
        GPIO.remove_event_detect(CLK_PIN)
        GPIO.cleanup()
