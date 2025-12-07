from typing import Optional, Tuple

import neopixel
import numpy as np

from fireplace.lights.utils import ColorMap


def create_pixel_index_map(shape: Tuple[int, int]) -> np.ndarray:
    """
    Pre-compute the mapping from linear pixel index to (row, col) in the color array.
    This avoids recalculating indices every frame.

    Args:
        shape: (rows, cols) of the LED matrix

    Returns:
        Array of shape (num_pixels, 2) containing [row, col] for each pixel index
    """
    rows, cols = shape
    num_pixels = rows * cols
    index_map = np.zeros((num_pixels, 2), dtype=np.int32)
    for i in range(num_pixels):
        # Row is inverted (bottom to top), column is standard (left to right)
        index_map[i, 0] = (rows - 1) - (i // cols)
        index_map[i, 1] = i % cols
    return index_map


# Pre-computed index map (lazily initialized)
_index_map: Optional[np.ndarray] = None
_index_map_shape: Optional[Tuple[int, int]] = None


def show_colors(pixels: neopixel.NeoPixel, temperature: np.ndarray, colormap: ColorMap):
    """
    Converts temperature values to color and shows them on the LEDs.

    Args:
        pixels (neopixel.NeoPixel): pixels object
        temperature (np.ndarray): temperature values. Values range from 0 to 1
        colormap (ColorMap): color map to translate temperature to colour
    """
    global _index_map, _index_map_shape

    coloured: np.ndarray = colormap(temperature)

    # Lazily create/update index map if shape changed
    if _index_map is None or _index_map_shape != coloured.shape[:2]:
        _index_map = create_pixel_index_map(coloured.shape[:2])
        _index_map_shape = coloured.shape[:2]

    # Vectorized pixel extraction: get all colors at once using advanced indexing
    rows = _index_map[:, 0]
    cols = _index_map[:, 1]
    flat_colors = coloured[rows, cols]

    # Assign all pixels at once (NeoPixel accepts slice assignment)
    # Using tolist() is faster than list comprehension as it's implemented in C
    pixels[:] = flat_colors.tolist()
    pixels.show()
