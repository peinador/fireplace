from pathlib import Path

from fireplace.lights.noise import (
    PerlinNoise,
    generate_noise_files,
    load_noise,
    noise_files_dir,
)

if __name__ == "__main__":
    n_files = 6
    width = 8
    length = 30 * 60 * 1
    generate_noise_files(noise_files_dir, n_files, length, width)

    print("testing loading")
    noise = load_noise(noise_files_dir)
    print(f"Loading was sucessful and the resulting array has shape {noise.shape}\n\n")
