from typing import List, Optional, Tuple, Union

import os
import random
from pathlib import Path

import numpy as np

noise_files_dir = Path(__file__).resolve().parents[2] / "data" / "perlin_noise"


def quadratic_mask(size, initial_value, final_value):
    """filter of the form a*y**2"""
    a = (final_value - initial_value) / (size[1] ** 2)
    sign = final_value > initial_value
    values = [initial_value + sign * a * (y**2) for y in range(size[1])]
    matrix = [values] * size[0]
    return np.array(matrix)


class PerlinNoise:
    def __init__(
        self, shape: tuple[int, int], repetition_period: int = 100, seed=42
    ) -> None:
        np.random.seed(seed)
        self.shape = shape
        self.angles = (
            2 * np.pi * np.random.rand(repetition_period + 1, repetition_period + 1)
        )
        self.repetition_period = repetition_period
        self.node_vectors = np.dstack((np.cos(self.angles), np.sin(self.angles)))

    def smooth_step(self, t):
        return 6 * t**5 - 15 * t**4 + 10 * t**3

    def generate_perlin_noise_2d(
        self, cell_size: tuple[int, int], pixel_offset: tuple[int, int] = (0, 0)
    ):
        # number of periods the fit in the shape
        periods: list[float, float] = [
            shape / cell_length for shape, cell_length in zip(self.shape, cell_size)
        ]
        grid_pixel_delta = [1 / cell_length for cell_length in cell_size]

        x_pixel_grid_axis = (
            np.linspace(0, periods[0], self.shape[0])
            + grid_pixel_delta[0] * pixel_offset[0]
        )
        y_pixel_grid_axis = (
            np.linspace(0, periods[1], self.shape[1])
            + grid_pixel_delta[1] * pixel_offset[1]
        )

        x_grid, y_grid = np.meshgrid(
            x_pixel_grid_axis, y_pixel_grid_axis, indexing="ij"
        )
        grid = np.dstack((x_grid, y_grid))

        # node vectors
        x_floor = np.floor(grid[:, :, 0]).astype(int) % self.repetition_period
        x_ceil = np.ceil(grid[:, :, 0]).astype(int) % self.repetition_period
        y_floor = np.floor(grid[:, :, 1]).astype(int) % self.repetition_period
        y_ceil = np.ceil(grid[:, :, 1]).astype(int) % self.repetition_period

        g00 = self.node_vectors[x_floor, y_floor]
        g10 = self.node_vectors[x_ceil, y_floor]
        g01 = self.node_vectors[x_floor, y_ceil]
        g11 = self.node_vectors[x_ceil, y_ceil]

        # intra-cell position vector
        internal_vector = grid % 1

        # dot product
        n00 = np.sum(internal_vector * g00, 2)
        n10 = np.sum(
            np.dstack((internal_vector[:, :, 0] - 1, internal_vector[:, :, 1])) * g10, 2
        )
        n01 = np.sum(
            np.dstack((internal_vector[:, :, 0], internal_vector[:, :, 1] - 1)) * g01, 2
        )
        n11 = np.sum(
            np.dstack((internal_vector[:, :, 0] - 1, internal_vector[:, :, 1] - 1))
            * g11,
            2,
        )

        # Interpolation
        smoothed_internal_position = self.smooth_step(internal_vector)
        n0 = (
            n00 * (1 - smoothed_internal_position[:, :, 0])
            + smoothed_internal_position[:, :, 0] * n10
        )
        n1 = (
            n01 * (1 - smoothed_internal_position[:, :, 0])
            + smoothed_internal_position[:, :, 0] * n11
        )

        output = (
            1 - smoothed_internal_position[:, :, 1]
        ) * n0 + smoothed_internal_position[:, :, 1] * n1
        return output

    def clip(self, noise: np.ndarray):
        return np.clip(noise, 0, 1)

    def postprocess(self, noise: np.ndarray):
        enhanced = 1.2 * (noise + 0.45)
        clipped = self.clip(enhanced)
        return clipped

    def render(
        self,
        octaves,
        pixel_offset=(0, 0),
        persistence: float = 0.5,
        relative_factor: float = 1.0,
    ):
        noise = np.zeros(self.shape)
        amplitude = 1
        size = min(self.shape)

        for mode in range(octaves):
            cell_size = (size, size * relative_factor)
            if min(cell_size) < 1:
                print(f"pixel size too small already at octave {mode}")
                break
            new_noise = self.generate_perlin_noise_2d(
                cell_size=cell_size, pixel_offset=pixel_offset
            )
            noise += amplitude * new_noise
            size = size // 2
            amplitude *= persistence

        return self.postprocess(noise)


def generate_noise_files(
    noise_files_dir: Union[str, os.PathLike], n_files: int, length: int, width: int = 8
) -> None:
    isExist = os.path.exists(noise_files_dir)
    if not isExist:
        os.makedirs(noise_files_dir)
    print()
    for file_no in range(n_files):
        perlin = PerlinNoise(
            shape=(length, width),
            repetition_period=length,
            seed=random.randint(0, 20000),
        )
        print(f"Generating file {file_no}...")
        noise = perlin.render(octaves=4, relative_factor=0.5)
        np.save(noise_files_dir / f"noise_{str(file_no)}.npy", noise)
        print("Generation and saving complete\n")

    print("Processed finished\n\n")


def load_noise(
    noise_files_dir: Union[str, os.PathLike], index: Optional[int] = None
) -> np.ndarray:
    files = os.listdir(noise_files_dir)
    if index is None:
        index = random.randint(0, len(files) - 1)
    assert index < len(files)
    filename = files[index]
    array = np.load(os.path.join(noise_files_dir, filename))
    return array
