from pytest import approx
from rai_digital_twin.types import TransformedTokenState
from rai_digital_twin.system_identification import VAR_prediction
import numpy as np



def test_VAR():
    N_samples = 10
    for _ in range(N_samples):
        N_rows = np.random.randint(3, 10)
        N_values = np.random.randint(3, 10)
        errors = np.random.randn(N_rows, N_values) + 5
        errors = np.array(errors)

        result = VAR_prediction(errors)
        assert result.shape[0] == N_values
