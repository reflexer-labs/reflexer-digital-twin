from pytest import approx

from rai_digital_twin.prepare_data import *


def test_interpolate():
    heights_per_timesteps = {
        0: 10,
        1: 19,
        2: 31,
        4: 42,
        5: 50
    }

    for timestep, height in heights_per_timesteps.items():
        interp_timestep = interpolate_timestep(heights_per_timesteps,
                                               height)
        assert interp_timestep == timestep

        interp_timestep = interpolate_timestep(heights_per_timesteps,
                                               height - 3)
        assert interp_timestep == timestep 

        interp_timestep = interpolate_timestep(heights_per_timesteps,
                                               height + 3)
        assert interp_timestep == (timestep + 1)
