import os
import time
from itertools import cycle
from logging import getLogger

import pygame

logger = getLogger(__name__)

AUDIO_FORMATS = [".mp3", ".wav"]


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
