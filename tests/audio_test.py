import signal
import time
from logging import getLogger

from fireplace.audio.audio_tools import AudioPlayer, get_audio_files

logger = getLogger(__name__)

AUDIO_PATH = "/home/pi/fireplace/data/audio_files"
MAX_TIME = 3600
VOLUME = 50  # 0-100

if __name__ == "__main__":
    stop = False

    def signal_handler(signum, frame):
        global stop
        stop = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    audio_files = get_audio_files(audio_path=AUDIO_PATH)

    def play_next_song():
        """Callback to play the next song when current one ends."""
        logger.info("Song Finished")
        audio_player.play(next(audio_files))

    audio_player = AudioPlayer(on_song_end=play_next_song)
    audio_player.set_volume(VOLUME)

    # Start playing
    audio_player.play(next(audio_files))

    start = time.time()
    try:
        while time.time() - start < MAX_TIME and not stop:
            time.sleep(0.1)  # Just wait, audio plays in background
    finally:
        audio_player.cleanup()
        print("Audio test finished")
