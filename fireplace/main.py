import logging
import os
import sys
import time
from itertools import cycle

import board
import neopixel
import numpy as np
import pygame
import RPi.GPIO as GPIO

from fireplace.audio.audio_tools import *
from fireplace.lights.led_comms import show_colors
from fireplace.lights.noise import load_noise, noise_files_dir, quadratic_mask
from fireplace.lights.utils import ColorMap, hex_to_rgb
from fireplace.rotary_encoder.rotary import Counter, create_encoder_callback

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("\r%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# CONFIGURATION

# rotary encoder
CLK_PIN = 23
DT_PIN = 8
CLK_Last = GPIO.HIGH
dtLastState = GPIO.HIGH

# audio
AUDIO_PATH = "/home/pi/fireplace/data/audio_files"
MAX_TIME = 3600
MUSIC_END = pygame.USEREVENT + 1
set_volume = lambda value: pygame.mixer.music.set_volume(value / 100 * 0.5)

# leds
TARGET_FPS = 60  # Target frames per second
FRAME_TIME = 1.0 / TARGET_FPS  # Time per frame in seconds
HEX_PALETTE = [
    "1f0900",
    "54370b",
    "754b03",
    "8e5318",
    "ad5c00",
    "d97b09",
    "fa9a2c",
    "fcb308",
]
# https://coolors.co/1f0900-54370b-754b03-8e5318-ad5c00-d97b09-fa9a2c-fcb308
rgb_palette = [hex_to_rgb(color) for color in HEX_PALETTE]
screen_size = (8, 8)
num_pixels = np.prod(screen_size)
pixel_pin = board.D12
COLOR_ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=COLOR_ORDER
)


def set_brightness(value):
    pixels.brightness = value / 100 * 0.5


if __name__ == "__main__":
    # init encoder
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    counter = Counter(
        value=80, range=(0, 100), step=2, callbacks=[set_volume, set_brightness]
    )
    encoder_callback = create_encoder_callback(counter, logger=logger)
    GPIO.add_event_detect(CLK_PIN, GPIO.BOTH, callback=encoder_callback)

    # init audio
    audio_files = get_audio_files(audio_path=AUDIO_PATH)
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(MUSIC_END)
    set_volume(counter.value)

    # init leds
    noise = load_noise(noise_files_dir)
    noise_back = load_noise(noise_files_dir)
    colormap = ColorMap(rgb_palette)
    test_mask = quadratic_mask(screen_size, 0.2, 1.2).T
    window = screen_size[1]
    max_step = noise.shape[0] - window
    step = 0

    try:
        play_next(audio_files)
        start = time.time()
        stop = False
        frame_start = time.time()
        while (time.time() - start < MAX_TIME) and not stop:
            for event in pygame.event.get():
                # A event will be hosted
                # after the end of every song
                if event.type == MUSIC_END:
                    logger.info("Song Finished")
                    play_next(audio_files)

                # Check user input
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_q:
                        stop = True

            if step < max_step:
                screen = noise[step : (step + window)]
            else:
                step = 0
                noise = noise_back
                max_step = noise.shape[0] - window
                noise_back = load_noise(noise_files_dir)
                screen = noise[step : (step + window)]
            step += 1
            temperature = screen * test_mask
            show_colors(pixels=pixels, temperature=temperature, colormap=colormap)

            # Frame rate control: sleep only the remaining time to hit target FPS
            elapsed = time.time() - frame_start
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            frame_start = time.time()

    except Exception as e:
        logger.critical(f"Encountered error {e}")
        time.sleep(10)
    finally:
        for i in range(num_pixels):
            pixels[i] = (0, 0, 0)
        pixels.show()
        print("Interrupted; Pixels Reset")
        pygame.quit()
        GPIO.remove_event_detect(CLK_PIN)
        GPIO.cleanup()
