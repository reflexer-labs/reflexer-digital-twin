from pytest import approx

from rai_digital_twin.prepare_data import *


def test_interpolate():
    heights_per_timesteps =[10, 19, 31, 42, 50]
    
    for timestep, height in enumerate(heights_per_timesteps):
        interp_timestep = interpolate_timestep(heights_per_timesteps,
                                               height)
        assert interp_timestep == timestep + 1

        interp_timestep = interpolate_timestep(heights_per_timesteps,
                                               height - 3)
        assert interp_timestep == timestep 

        interp_timestep = interpolate_timestep(heights_per_timesteps,
                                               height + 3)
        assert interp_timestep == timestep + 1

