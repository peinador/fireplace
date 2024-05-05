from typing import List, Tuple

import neopixel
import numpy as np

from fireplace.lights.utils import ColorMap


def show_colors(pixels: neopixel.NeoPixel, temperature: np.ndarray, colormap: ColorMap):
    """
    converts temperature values to color and shows them on the leds

    Args:
        pixels (neopixel.NeoPixel): pixels object
        temperature (List): temperature values. Values range from 0 to 1
        colormap (ColorMap):  color map to translate temperature to colour
    """
    coloured: np.ndarray = colormap(temperature)
    for i in range(len(pixels)):
        row = (coloured.shape[0] - 1) - (i // coloured.shape[1])
        col = i % coloured.shape[1]
        pixels[i] = list(coloured[row, col, :])
    pixels.show()
