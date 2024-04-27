from typing import List, Tuple

import abc
import random
from math import pi, prod, sin

import numpy as np

from fireplace.lights.noise import PerlinNoise, quadratic_mask


class Animation(abc.ABC):
    """Base class for animations. The main use is to obtain list of colors
    to display in the LED matrix. The list of outputs will be encoded
    in

    """

    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self.state = self.initial_state()
        self.cumm_time = 0

    @abc.abstractmethod
    def initial_state(self):
        pass

    @abc.abstractmethod
    def evolve(self, step):
        pass

    def map_pixel(self, position: Tuple) -> int:
        """Maps the position of a pixel in the matrix to the linear position.
        Works for any dimension

        Args:
            position (Tuple): position of the pixel in format (row, column)

        Returns:
            int: one-dimensional index of the pixel
        """
        return sum([position[i] * prod(self.size[0:i]) for i in range(len(position))])


class Wave(Animation):
    def __init__(self, size: tuple[int], cycle: float = 30) -> None:
        self.cycle = cycle
        super().__init__(size)

    def initial_state(self):
        return self.compute_colors(0)

    def compute_colors(self, shift: int = 0):
        colors = []
        for row in range(self.size[0]):
            x = row / self.size[0]
            for col in range(self.size[1]):
                colors.append((1 + sin((x + shift) * 2 * pi)) / 2)
        return colors

    def evolve(self, step: float) -> list[tuple[int, int, int]]:
        self.cumm_time += step
        new_colors = self.compute_colors(self.cumm_time / self.cycle)
        return new_colors


class JustFLicker(Animation):
    def __init__(self, size: tuple[int], std: float = 0.05) -> None:
        super().__init__(size)
        self.std = std

    def initial_state(self):
        return [0.5] * prod(self.size)

    def evolve(self, step):
        color = random.gauss(0.5, self.std)
        color = max(0, color)
        color = min(1, color)
        return [color] * prod(self.size)


class Flames(Animation):
    def __init__(self, size: tuple[int]) -> None:
        super().__init__(size)
        self.perlin = PerlinNoise(shape=size)
        self.mask = quadratic_mask(size=size, initial_value=0.6, final_value=1.2)
        self.shift = 0

    def evolve(self, step: float):
        self.shift += step
        noise = self.perlin.render(octaves=4, pixel_offset=(0, int(self.shift)))
        masked_noise = noise * self.mask
        self.state = masked_noise
        return self.state

    def initial_state(self):
        return np.zeros(self.size)
