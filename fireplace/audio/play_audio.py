import os
import time
from itertools import cycle

import pygame
from loguru import logger

AUDIO_PATH = "/home/pi/fireplace/data/fireplace_mp3"
# AUDIO_PATH = "/home/pi/fireplace/data/sample.mp3"
AUDIO_FORMATS = [".mp3", ".wav"]
MAX_TIME = 3600
MUSIC_END = pygame.USEREVENT + 1
volume = 1.0


def is_audio_file(path: str):
    extension = os.path.splitext(path)[1]
    return extension in AUDIO_FORMATS


def play_next(audio_files):
    toplay = next(audio_files)
    logger.info(f"Now playing...\n{toplay}")
    pygame.mixer.music.load(toplay)
    pygame.mixer.music.play()


def get_audio_files(audio_path):
    if os.path.isdir(audio_path):
        files = [
            f
            for f in os.listdir(audio_path)
            if os.path.isfile(os.path.join(audio_path, f))
        ]
        audio_files = [os.path.join(audio_path, f) for f in files if is_audio_file(f)]
        audio_files = sorted(audio_files)
    else:
        assert is_audio_file(audio_path)
        audio_files = [audio_path]

    n_clips = len(audio_files)
    logger.info(f"Audio files found: {n_clips}")

    audio_files = cycle(audio_files)
    return audio_files


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
