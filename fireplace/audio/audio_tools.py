import os
import subprocess
import threading
from itertools import cycle
from logging import getLogger
from typing import Callable, Iterator, Optional

logger = getLogger(__name__)

AUDIO_FORMATS = [".mp3", ".wav"]


def detect_i2s_device() -> str:
    """
    Auto-detect the I2S audio device.
    Returns the first non-HDMI hardware device found, or 'default' as fallback.
    """
    try:
        result = subprocess.run(
            ["aplay", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "default"

        # Parse aplay -l output to find I2S device
        # Example: "card 1: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar], device 0: ..."
        for line in result.stdout.split("\n"):
            if line.startswith("card "):
                # Skip HDMI devices
                if "hdmi" in line.lower() or "vc4" in line.lower():
                    continue
                # Extract card name
                # Format: "card N: NAME [DESCRIPTION], device M: ..."
                parts = line.split(":")
                if len(parts) >= 2:
                    card_part = parts[0]  # "card N"
                    name_part = parts[1].split("[")[0].strip()  # "NAME"
                    card_num = card_part.replace("card ", "").strip()
                    device = f"plughw:CARD={name_part},DEV=0"
                    logger.info(f"Auto-detected I2S audio device: {device}")
                    return device

        return "default"
    except Exception as e:
        logger.warning(f"Failed to auto-detect audio device: {e}")
        return "default"


def get_alsa_device() -> str:
    """
    Get the ALSA device to use for audio playback.
    Uses ALSA_DEVICE env var if set, otherwise auto-detects.
    """
    env_device = os.environ.get("ALSA_DEVICE")
    if env_device:
        logger.info(f"Using ALSA device from environment: {env_device}")
        return env_device

    return detect_i2s_device()




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
        self._current_filepath: Optional[str] = None
        # Auto-detect ALSA device on first instantiation
        self._alsa_device = get_alsa_device()

    def play(self, filepath: str) -> None:
        """Play an audio file."""
        self.stop()  # Stop any currently playing audio

        ext = os.path.splitext(filepath)[1].lower()
        logger.info(f"Now playing: {filepath}")

        if not os.path.exists(filepath):
            logger.error(f"Audio file not found: {filepath}")
            return

        # Calculate volume factor (mpg123 uses 0-32768, we scale from 0-100)
        volume_factor = int((self._volume / 100) * 32768)
        logger.info(f"Playing with volume {self._volume}% (factor: {volume_factor})")

        if ext == ".mp3":
            # mpg123: -o alsa forces ALSA, -a specifies device, --no-control disables terminal
            cmd = [
                "mpg123",
                "-o", "alsa",
                "-a", self._alsa_device,
                "--no-control",
                "-f", str(volume_factor),
                filepath,
            ]
        elif ext == ".wav":
            # aplay for WAV files, specify device explicitly
            cmd = ["aplay", "-q", "-D", self._alsa_device, filepath]
        else:
            logger.warning(f"Unsupported format: {ext}")
            return

        self._current_filepath = filepath

        try:
            self._stopping = False
            # Capture stderr to diagnose issues
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
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

        # Wait for process to finish and capture stderr
        _, stderr = self._process.communicate()
        exit_code = self._process.returncode

        # Log any errors
        if exit_code != 0:
            stderr_text = stderr.decode() if stderr else ""
            logger.warning(f"Audio player exited with code {exit_code}")
            if stderr_text:
                logger.warning(f"Audio player stderr: {stderr_text[:200]}")

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
        Set the playback volume (0-100).
        Volume is applied via mpg123's -f flag on next play.
        """
        self._volume = max(0, min(100, volume))

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._process is not None and self._process.poll() is None

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
