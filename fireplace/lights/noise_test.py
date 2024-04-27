# %%
from typing import List, Tuple

from time import sleep

import numpy as np
from matplotlib import pyplot as plt

from fireplace.lights.noise import PerlinNoise

perlin = PerlinNoise(shape=(8, 8))

noise = perlin.render(octaves=5, pixel_offset=(0, 10))

print(noise)
plt.imshow(noise.T)

"""for shift in range(40):
    noise = perlin.render(octaves=5,pixel_offset=(0,shift))
    plt.imshow(noise.T)
    plt.show()  # show the plot
    sleep(0.0)  # pause for a second
    clear_output(wait=True)  # clear the output for the next loop"""
# print(p)
# %%
