"""Fireplace controller class for programmatic control of the fireplace animation."""

import logging
import threading
import time
from typing import Optional

import board
import neopixel
import numpy as np
import RPi.GPIO as GPIO

from fireplace.audio.audio_tools import AudioPlayer, get_audio_files
from fireplace.lights.led_comms import show_colors
from fireplace.lights.noise import load_noise, noise_files_dir, quadratic_mask
from fireplace.lights.utils import ColorMap, hex_to_rgb
from fireplace.rotary_encoder.rotary import Counter, create_encoder_callback

# Configure logging
logger = logging.getLogger(__name__)


class BackgroundNoiseLoader:
    """Loads noise files in a background thread to avoid blocking the main loop."""

    def __init__(self, noise_dir):
        self.noise_dir = noise_dir
        self._noise_buffer = None
        self._lock = threading.Lock()
        self._loading = False

    def start_loading(self):
        """Start loading a noise file in the background."""
        if self._loading:
            return  # Already loading
        self._loading = True
        thread = threading.Thread(target=self._load_noise, daemon=True)
        thread.start()

    def _load_noise(self):
        """Background thread that loads the noise file."""
        noise = load_noise(self.noise_dir)
        with self._lock:
            self._noise_buffer = noise
            self._loading = False

    def get_noise(self):
        """
        Get the loaded noise if available, otherwise load synchronously.
        Returns the noise array and starts loading the next one.
        """
        with self._lock:
            if self._noise_buffer is not None:
                noise = self._noise_buffer
                self._noise_buffer = None
            else:
                # Fallback: load synchronously if buffer is empty
                noise = load_noise(self.noise_dir)
        # Start loading next noise file in background
        self.start_loading()
        return noise


# Configuration constants
CLK_PIN = 23
DT_PIN = 8
AUDIO_PATH = "/home/pi/fireplace/data/audio_files"
TARGET_FPS = 32
FRAME_TIME = 1.0 / TARGET_FPS
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
SCREEN_SIZE = (8, 8)
NUM_PIXELS = np.prod(SCREEN_SIZE)
PIXEL_PIN = board.D12
COLOR_ORDER = neopixel.GRB


class Fireplace:
    """
    Controls the fireplace animation including LEDs, audio, and rotary encoder.

    The fireplace runs in a background thread and can be started/stopped via API.
    """

    def __init__(self):
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_time: Optional[float] = None
        self._duration_seconds: Optional[float] = None
        self._lock = threading.Lock()

        # Hardware references (initialized on start)
        self._pixels: Optional[neopixel.NeoPixel] = None
        self._audio_player: Optional[AudioPlayer] = None
        self._counter: Optional[Counter] = None

    @property
    def is_running(self) -> bool:
        """Check if the fireplace is currently running."""
        return self._running

    @property
    def remaining_seconds(self) -> int:
        """Get remaining time in seconds, or 0 if not running."""
        if (
            not self._running
            or self._start_time is None
            or self._duration_seconds is None
        ):
            return 0
        elapsed = time.time() - self._start_time
        remaining = self._duration_seconds - elapsed
        return max(0, int(remaining))

    def start(self, duration_minutes: float = 60) -> bool:
        """
        Start the fireplace animation.

        Args:
            duration_minutes: How long to run the animation in minutes.

        Returns:
            True if started successfully, False if already running.
        """
        with self._lock:
            if self._running:
                logger.warning("Fireplace is already running")
                return False

            self._running = True
            self._stop_event.clear()
            self._duration_seconds = duration_minutes * 60
            self._start_time = time.time()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Fireplace started for {duration_minutes} minutes")
        return True

    def stop(self) -> bool:
        """
        Stop the fireplace animation.

        Returns:
            True if stopped successfully, False if not running.
        """
        with self._lock:
            if not self._running:
                logger.warning("Fireplace is not running")
                return False

        logger.info("Stopping fireplace...")
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

        return True

    def wait(self):
        """Block until the fireplace stops (either naturally or via stop())."""
        if self._thread is not None:
            self._thread.join()

    def _set_brightness(self, value: float):
        """Set LED brightness (0-100)."""
        if self._pixels is not None:
            self._pixels.brightness = value / 100 * 0.5

    def _set_volume(self, value: float):
        """Set audio volume (0-100)."""
        if self._audio_player is not None:
            self._audio_player.set_volume(int(value))

    def _run_loop(self):
        """Main animation loop (runs in background thread)."""
        try:
            self._initialize_hardware()
            self._animation_loop()
        except Exception as e:
            logger.critical(f"Encountered error: {e}")
        finally:
            self._cleanup()
            with self._lock:
                self._running = False
                self._start_time = None
                self._duration_seconds = None

    def _initialize_hardware(self):
        """Initialize all hardware components."""
        # Initialize NeoPixels
        self._pixels = neopixel.NeoPixel(
            PIXEL_PIN,
            NUM_PIXELS,
            brightness=0.2,
            auto_write=False,
            pixel_order=COLOR_ORDER,
        )

        # Initialize audio
        audio_files = get_audio_files(audio_path=AUDIO_PATH)

        def play_next_song():
            logger.info("Song finished")
            if self._audio_player is not None and not self._stop_event.is_set():
                self._audio_player.play(next(audio_files))

        self._audio_player = AudioPlayer(on_song_end=play_next_song)

        # Initialize rotary encoder
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._counter = Counter(
            value=80,
            range=(0, 100),
            step=2,
            callbacks=[self._set_volume, self._set_brightness],
        )
        encoder_callback = create_encoder_callback(self._counter, logger=logger)
        GPIO.add_event_detect(CLK_PIN, GPIO.BOTH, callback=encoder_callback)

        # Set initial volume
        self._set_volume(self._counter.value)

        # Start playing first song
        self._audio_player.play(next(audio_files))

        logger.info("Hardware initialized")

    def _animation_loop(self):
        """Run the LED animation loop."""
        rgb_palette = [hex_to_rgb(color) for color in HEX_PALETTE]
        noise_loader = BackgroundNoiseLoader(noise_files_dir)
        noise = noise_loader.get_noise()
        colormap = ColorMap(rgb_palette)
        test_mask = quadratic_mask(SCREEN_SIZE, 0.2, 1.2).T
        window = SCREEN_SIZE[1]
        max_step = noise.shape[0] - window
        step = 0

        frame_start = time.time()

        while not self._stop_event.is_set():
            # Check if duration has elapsed
            if self._duration_seconds is not None and self._start_time is not None:
                if time.time() - self._start_time >= self._duration_seconds:
                    logger.info("Duration elapsed, stopping")
                    break

            # Update animation frame
            if step < max_step:
                screen = noise[step : (step + window)]
            else:
                step = 0
                noise = noise_loader.get_noise()
                max_step = noise.shape[0] - window
                screen = noise[step : (step + window)]

            step += 1
            temperature = screen * test_mask
            show_colors(pixels=self._pixels, temperature=temperature, colormap=colormap)

            # Frame rate control
            elapsed = time.time() - frame_start
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            frame_start = time.time()

    def _cleanup(self):
        """Clean up all hardware resources."""
        logger.info("Cleaning up hardware...")

        # Turn off LEDs
        if self._pixels is not None:
            try:
                self._pixels.fill((0, 0, 0))
                self._pixels.show()
            except Exception:
                pass
            self._pixels = None

        # Stop audio
        if self._audio_player is not None:
            self._audio_player.cleanup()
            self._audio_player = None

        # Clean up GPIO - only the pins we used, not global cleanup
        # Global cleanup interferes with NeoPixel and prevents restart
        try:
            GPIO.remove_event_detect(CLK_PIN)
        except Exception:
            pass
        try:
            GPIO.cleanup([CLK_PIN, DT_PIN])
        except Exception:
            pass

        self._counter = None
        logger.info("Cleanup complete")
