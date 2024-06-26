import time

import board
import neopixel
import numpy as np

from fireplace.lights.led_comms import show_colors
from fireplace.lights.noise import load_noise, noise_files_dir, quadratic_mask
from fireplace.lights.utils import ColorMap, hex_to_rgb

# https://coolors.co/260c02-542c0b-802c08-be320b-f48405-ffa632
HEX_PALETTE = [
    "1f0900",
    "542c0b",
    "873f01",
    "984c00",
    "ad5c00",
    "d95b08",
    "f48405",
    "fcb308",
]

rgb_palette = [hex_to_rgb(color) for color in HEX_PALETTE]

screen_size = (8, 8)
num_pixels = np.prod(screen_size)

noise = load_noise(noise_files_dir)
noise_back = load_noise(noise_files_dir)

colormap = ColorMap(rgb_palette)

test_mask = quadratic_mask(screen_size, 0.2, 1.2).T

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D12
# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)


if __name__ == "__main__":
    import cProfile
    from pstats import Stats

    pr = cProfile.Profile()
    pr.enable()

    print("Ready to play")

    try:
        old_time = time.time()
        intervals = []
        window = screen_size[1]
        max_step = noise.shape[0] - window
        step = 0
        while True:
            # time.sleep(wait)
            new_time = time.time()
            time_interval = new_time - old_time
            intervals.append(time_interval)
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
            old_time = new_time

    except KeyboardInterrupt:
        pr.disable()
        for i in range(num_pixels):
            pixels[i] = (0, 0, 0)
        pixels.show()
        print("Interrupted; Pixels Reset")
        stats = Stats(pr)
        stats.sort_stats("tottime").print_stats(10)
        print(f"\n\nAverage iteration time:{np.mean(intervals)}")
