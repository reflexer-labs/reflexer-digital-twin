from cadCAD_tools import easy_run
from rai_digital_twin import default_model
from rai_digital_twin.backtesting import VALIDATION_METRICS, generic_loss, simulation_loss, simulation_metrics_loss, validation_loss

from pytest import approx

def test_identical_backtesting():

    # Run the model on default arguments
    sim_df = easy_run(*default_model.run_args,
                  assign_params=False)
    test_df = sim_df.copy()

    cols = sim_df.dtypes
    numeric_inds = (cols == float) | (cols == int)
    numeric_cols = cols[numeric_inds].index

    # Assert that the loss when testing a dataframe against itself gives
    # null losses for each numerical column
    for col in numeric_cols:
        assert generic_loss(sim_df, test_df, col) == approx(0.0, 1e-5)

    # Assert consistency of the simulation metrics loss
    sim_metrics_losses = simulation_metrics_loss(sim_df, test_df)
    assert sim_metrics_losses.keys()  == VALIDATION_METRICS.keys()
    assert sum(type(v) is float for v in sim_metrics_losses.values()) == len(sim_metrics_losses)

    # Assert that the simulation loss is consistent
    assert simulation_loss(sim_df, test_df) == approx(0.0, 1e-5)
    
    
def test_semi_identical_backtesting():
    # Run the model on default arguments
    sim_df = easy_run(*default_model.run_args,
                  assign_params=False)

    # Filter for only the numerical cols
    cols = sim_df.dtypes
    numeric_inds = (cols == float) | (cols == int)
    numeric_cols = cols[numeric_inds].index
    sim_df = sim_df.loc[:, numeric_cols]

    # Test df is all simulation values multiplied by K
    test_df_1 = sim_df * 2
    test_df_2 = sim_df * 3

    # Loss must be larger than if it was the simulation df against itself
    assert simulation_loss(sim_df, test_df_1) > simulation_loss(sim_df, sim_df)
    assert simulation_loss(sim_df, test_df_2) > simulation_loss(sim_df, sim_df)

    # Loss must be commutative
    assert simulation_loss(sim_df, test_df_1) == simulation_loss(test_df_1, sim_df)
    assert simulation_loss(test_df_2, sim_df) == simulation_loss(sim_df, test_df_2)
    assert simulation_loss(test_df_2, test_df_1) == simulation_loss(test_df_1, test_df_2)


