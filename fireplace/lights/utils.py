from typing import List, Tuple

import numpy as np


def hex_to_rgb(hex: str):
    nohash_hex = hex.lstrip("#")
    rgb = tuple(int(nohash_hex[i : i + 2], 16) for i in (0, 2, 4))
    return rgb


class ColorMap:
    def __init__(self, palette: list[tuple[int, int, int]], gamma: float = 2.8) -> None:
        """Args:
        palette (list): List of colors to interpolate. Each element is an
        RGB color encoded as a tuple. The first color would be assumed to be
        0 and the last one assume to be 1.
        """
        self.palette = palette
        self._palette = np.asarray(
            palette + [palette[-1]]
        )  # repeat last element to avoid index overflow when hitting maximum value
        self.gamma = gamma
        self.ncols = len(palette)
        self.generate_gamma_correction_table()

    def generate_gamma_correction_table(self):
        values = list(range(256))
        corrected_values = [
            int(255 * (value / 255) ** (self.gamma)) for value in values
        ]
        self.gamma_correction_table = np.asarray(corrected_values)

    @staticmethod
    def interpolate_two_colors(x: np.ndarray, color1: np.ndarray, color2: np.ndarray):
        expanded_x = np.repeat(x[..., np.newaxis], 3, axis=-1)
        interpolation = color1 + (color2 - color1) * expanded_x
        result = np.round(interpolation).astype(int)
        return result

    def gamma_correction(self, color: tuple[int, int, int]):
        # apply gamma correction
        # gamma_corrected_color = tuple([
        #         self.gamma_correction_table[val] for val in color
        #    ])
        gamma_corrected_color = self.gamma_correction_table[color]
        return gamma_corrected_color

    def __call__(self, x: np.ndarray) -> tuple[int, int, int]:
        x = x.clip(0, 1)
        start_color_index = np.floor(x * (self.ncols - 1)).astype(int)
        # assert start_color_index < self.ncols-1
        rebased_x = x * (self.ncols - 1) % 1
        return_color = self.interpolate_two_colors(
            rebased_x,
            self._palette[start_color_index],
            self._palette[start_color_index + 1],
        )
        return self.gamma_correction(return_color)
