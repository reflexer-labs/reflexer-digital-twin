from cadCAD_tools import easy_run
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin import default_model


def test_execution():

    N_t = 5
    N_s = 2
    expected_rows_count = (N_t + 1) * N_s
    results = easy_run(default_model.initial_state,
                       prepare_params(default_model.parameters),
                       default_model.timestep_block,
                       N_t,
                       N_s,
                       assign_params=False)
    assert len(results) == expected_rows_count
