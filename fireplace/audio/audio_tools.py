import os
import subprocess
import threading
from collections.abc import Iterator
from itertools import cycle
from logging import getLogger
from typing import Callable, Optional

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
                    name_part = parts[1].split("[")[0].strip()  # "NAME"
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
    Lightweight audio player using mpg123 in remote control mode.
    Supports real-time volume control via stdin commands.
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
        self._lock = threading.Lock()
        # Auto-detect ALSA device on first instantiation
        self._alsa_device = get_alsa_device()

    def _ensure_process(self) -> bool:
        """Ensure mpg123 remote process is running. Returns True if ready."""
        if self._process is not None and self._process.poll() is None:
            return True

        try:
            # Start mpg123 in remote control mode
            # -R: remote control mode (reads commands from stdin)
            # -o alsa: use ALSA output
            # -a: specify device
            cmd = [
                "mpg123",
                "-R",
                "-o",
                "alsa",
                "-a",
                self._alsa_device,
            ]
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            logger.info("Started mpg123 in remote control mode")

            # Set initial volume
            self._send_command(f"VOLUME {self._volume}")

            return True
        except FileNotFoundError:
            logger.error("mpg123 not found. Install with: sudo apt-get install mpg123")
            return False
        except Exception as e:
            logger.error(f"Failed to start mpg123: {e}")
            return False

    def _send_command(self, command: str) -> None:
        """Send a command to mpg123 remote control."""
        if self._process is None or self._process.stdin is None:
            return
        try:
            with self._lock:
                self._process.stdin.write(command + "\n")
                self._process.stdin.flush()
            logger.debug(f"Sent command: {command}")
        except (BrokenPipeError, OSError) as e:
            logger.warning(f"Failed to send command: {e}")

    def play(self, filepath: str) -> None:
        """Play an audio file."""
        ext = os.path.splitext(filepath)[1].lower()

        if not os.path.exists(filepath):
            logger.error(f"Audio file not found: {filepath}")
            return

        if ext != ".mp3":
            logger.warning(f"Remote mode only supports MP3, got: {ext}")
            return

        if not self._ensure_process():
            return

        self._stopping = False
        logger.info(f"Now playing: {filepath} at volume {self._volume}%")

        # Load and play the file
        self._send_command(f"LOAD {filepath}")

        # Start monitoring thread to detect when song ends
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_thread = threading.Thread(
                target=self._monitor_playback, daemon=True
            )
            self._monitor_thread.start()

    def _monitor_playback(self) -> None:
        """Monitor mpg123 output to detect when songs end."""
        if self._process is None or self._process.stdout is None:
            return

        try:
            for line in self._process.stdout:
                line = line.strip()
                # @P 0 = playback stopped (song finished)
                # @P 1 = playback paused
                # @P 2 = playback playing
                if line == "@P 0" and not self._stopping:
                    logger.info("Song finished")
                    if self._on_song_end:
                        self._on_song_end()
                # @E = error messages
                elif line.startswith("@E"):
                    logger.warning(f"mpg123 error: {line}")
        except Exception as e:
            if not self._stopping:
                logger.warning(f"Monitor thread error: {e}")

    def stop(self) -> None:
        """Stop the currently playing audio."""
        self._stopping = True
        self._send_command("STOP")

    def set_volume(self, volume: int) -> None:
        """
        Set the playback volume (0-100).
        Takes effect immediately on currently playing audio.
        """
        self._volume = max(0, min(100, volume))
        self._send_command(f"VOLUME {self._volume}")
        logger.debug(f"Volume set to {self._volume}%")

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._process is not None and self._process.poll() is None

    def cleanup(self) -> None:
        """Clean up resources."""
        self._stopping = True
        if self._process is not None:
            self._send_command("QUIT")
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
