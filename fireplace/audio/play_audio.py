import os
import time
from itertools import cycle
from logging import getLogger

import pygame

from fireplace.audio.audio_tools import *

logger = getLogger(__name__)

AUDIO_PATH = "/home/pi/fireplace/data/fireplace_mp3"
AUDIO_FORMATS = [".mp3", ".wav"]
MAX_TIME = 3600
MUSIC_END = pygame.USEREVENT + 1
volume = 1.0

if __name__ == "__main__":
    audio_files = get_audio_files(audio_path=AUDIO_PATH)
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(MUSIC_END)
    pygame.mixer.music.set_volume(volume)

    play_next(audio_files)

    start = time.time()
    while time.time() - start < MAX_TIME:
        for event in pygame.event.get():
            # A event will be hosted
            # after the end of every song
            if event.type == MUSIC_END:
                logger.info("Song Finished")
                play_next(audio_files)

            # Check user input
            # if Return or Q, quit pygame
            elif event.type == pygame.event.KEYDOWN:
                if event.key == "K_RETURN" or event.key == "K_q":
                    pygame.quit()
    pygame.quit()
