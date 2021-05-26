from pytest import approx
from rai_digital_twin.types import ActionState, ControllerState, TokenState, TransformedTokenState, UserActionParams
from rai_digital_twin.system_identification import VAR_prediction, fit_predict_action
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


def test_fit_predict():

    state_1 = {'token_state': TokenState(10, 10, 5, 5),
               'pid_state': ControllerState(1.2, 1.01, 0.5, 0.5),
               'market_price': 1.1,
               'eth_price': 0.9
               }

    state_2 = {'token_state': TokenState(12, 8, 4, 3),
               'pid_state': ControllerState(0.8, 0.99, 0.5, 0.5),
               'market_price': 2.0,
               'eth_price': 0.4
               }

    state_3 = {'token_state': TokenState(12, 9, 4, 10),
               'pid_state': ControllerState(0.8, 0.99, 0.5, 0.5),
               'market_price': 2.2,
               'eth_price': 0.4
               }

    state_4 = {'token_state': TokenState(12, 9, 4, 10),
               'pid_state': ControllerState(0.8, 0.99, 0.5, 0.5),
               'market_price': 0.5,
               'eth_price': 1.2
               }

    state_5 = {'token_state': TokenState(12, 8, 4, 3),
               'pid_state': ControllerState(0.8, 0.99, 0.5, 0.5),
               'market_price': 2.0,
               'eth_price': 0.4
               }
               
    states = [
        ActionState(**state_1),
        ActionState(**state_2),
        ActionState(**state_3),
        ActionState(**state_4),
        ActionState(**state_5)
    ]

    params = UserActionParams(1.0, 100, 0.003, True, 1.0)

    new_action = fit_predict_action(states, params)
    assert type(new_action) == TokenState
