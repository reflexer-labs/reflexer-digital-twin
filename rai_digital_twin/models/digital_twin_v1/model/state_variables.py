from cadCAD_tools.types import InitialValue
from cadCAD_tools.preparation import prepare_state
from rai_digital_twin.types import ControllerParams, ControllerState, TokenState
from rai_digital_twin.types import USD_per_RAI, Seconds, Height, USD_per_ETH

INITIAL_ETH_PRICE: USD_per_ETH = 5.0
INITIAL_MARKET_PRICE: USD_per_RAI = 5.1

INITIAL_CONTROLLER_PARAMS = ControllerParams(ki=2e-7,
                                             kp=0.0,
                                             leaky_factor=1.0,
                                             period=4 * 60 * 60,
                                             enabled=True)

INITIAL_CONTROLLER_STATE = ControllerState(redemption_price=4.9,
                                           redemption_rate=0.2,
                                           proportional_error=0.0,
                                           integral_error=0.0)

INITIAL_TOKEN_STATE = TokenState(rai_reserve=1e5,
                                 eth_reserve=1e5,
                                 rai_debt=2e5,
                                 eth_locked=1e5)

# NB: These initial states may be overriden in the relevant notebook or experiment process
raw_state_variables: dict[str, InitialValue] = {
    # Time states
    'timedelta': InitialValue(0, Seconds),
    'cumulative_time': InitialValue(0, Seconds),
    'blockheight': InitialValue(0, Height),

    # Exogenous states
    'eth_price': InitialValue(INITIAL_ETH_PRICE, USD_per_ETH),
    'market_price_twap': InitialValue(INITIAL_MARKET_PRICE, USD_per_RAI),

    # Controller state
    'pid_params': InitialValue(INITIAL_CONTROLLER_PARAMS, ControllerParams),
    'pid_state': InitialValue(INITIAL_CONTROLLER_STATE, ControllerState),

    # RAI token state
    'token_state': InitialValue(INITIAL_TOKEN_STATE, TokenState)

}

state_variables = prepare_state(raw_state_variables)
