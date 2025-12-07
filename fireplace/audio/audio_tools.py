import os
import subprocess
import threading
from itertools import cycle
from logging import getLogger
from typing import Callable, Iterator, Optional

logger = getLogger(__name__)

AUDIO_FORMATS = [".mp3", ".wav"]


def is_audio_file(path: str) -> bool:
    extension = os.path.splitext(path)[1].lower()
    return extension in AUDIO_FORMATS


def get_audio_files(audio_path: str) -> Iterator[str]:
    """Get an infinite iterator of audio files from a path."""
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

    return cycle(audio_files)


class AudioPlayer:
    """
    Lightweight audio player using subprocess.
    Uses mpg123 for MP3 files and aplay for WAV files.
    Much lighter than pygame's full SDL stack.
    """

    def __init__(self, on_song_end: Optional[Callable[[], None]] = None):
        """
        Args:
            on_song_end: Optional callback called when a song finishes playing.
        """
        self._process: Optional[subprocess.Popen] = None
        self._on_song_end = on_song_end
        self._volume = 50  # 0-100
        self._monitor_thread: Optional[threading.Thread] = None
        self._stopping = False

    def play(self, filepath: str) -> None:
        """Play an audio file."""
        self.stop()  # Stop any currently playing audio

        ext = os.path.splitext(filepath)[1].lower()
        logger.info(f"Now playing: {filepath}")

        if ext == ".mp3":
            # mpg123: -q for quiet mode
            cmd = ["mpg123", "-q", filepath]
        elif ext == ".wav":
            # aplay for WAV files
            cmd = ["aplay", "-q", filepath]
        else:
            logger.warning(f"Unsupported format: {ext}")
            return

        try:
            self._stopping = False
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            # Start monitoring thread to detect when song ends
            self._monitor_thread = threading.Thread(
                target=self._monitor_playback, daemon=True
            )
            self._monitor_thread.start()
        except FileNotFoundError:
            logger.error(f"Audio player command not found: {cmd[0]}")
            logger.error("Install with: sudo apt-get install mpg123")

    def _monitor_playback(self) -> None:
        """Monitor the subprocess and call callback when it ends."""
        if self._process is None:
            return
        self._process.wait()
        if not self._stopping and self._on_song_end:
            self._on_song_end()

    def stop(self) -> None:
        """Stop the currently playing audio."""
        self._stopping = True
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def set_volume(self, volume: int) -> None:
        """
        Set the system volume (0-100).
        Uses ALSA amixer to control the volume.
        """
        self._volume = max(0, min(100, volume))
        try:
            # Try common ALSA mixer controls
            for control in ["PCM", "Master", "Speaker"]:
                result = subprocess.run(
                    ["amixer", "sset", control, f"{self._volume}%"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logger.debug(f"Volume set to {self._volume}% via {control}")
                    return
            logger.warning("Could not set volume via amixer")
        except FileNotFoundError:
            logger.warning("amixer not found, volume control unavailable")

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._process is not None and self._process.poll() is None

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
