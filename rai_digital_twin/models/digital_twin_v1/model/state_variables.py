from cadCAD_tools.types import InitialValue
from cadCAD_tools.preparation import prepare_params, prepare_state
from rai_digital_twin.types import Seconds, Height, USD_per_ETH
from rai_digital_twin.types import ETH, RAI, Percentage
from rai_digital_twin.types import USD_per_RAI, USD_Seconds_per_RAI

INITIAL_ETH_PRICE: USD_per_ETH = 5.0
INITIAL_REDEMPTION_PRICE: USD_per_RAI = 4.9
INITIAL_REDEMPTION_RATE: Percentage = 0.2

INITIAL_ETH_RESERVE: ETH = 100
INITIAL_RAI_RESERVE: RAI = 100
INITIAL_ETH_LOCKED: ETH = 100
INITIAL_RAI_DRAWN: RAI = 200

INITIAL_P_ERROR: USD_per_RAI = 0.0
INITIAL_I_ERROR: USD_Seconds_per_RAI = 0.0
INITIAL_STABILITY_FEE: Percentage = 0.03
INITIAL_MARKET_PRICE: USD_per_RAI = 5.1


# NB: These initial states may be overriden in the relevant notebook or experiment process
raw_state_variables: dict[str, InitialValue] = {
    # Time states
    'timedelta': InitialValue(0, Seconds),
    'cumulative_time': InitialValue(0, Seconds),
    'blockheight': InitialValue(0, Height),

    # Exogenous states
    'eth_price': InitialValue(INITIAL_ETH_PRICE, USD_per_ETH),

    # Controller states
    'market_price_twap': InitialValue(INITIAL_MARKET_PRICE, USD_per_RAI),
    'redemption_price': InitialValue(INITIAL_REDEMPTION_PRICE, USD_per_RAI),
    'redemption_rate': InitialValue(INITIAL_REDEMPTION_RATE, Percentage),
    'error_star': InitialValue(INITIAL_P_ERROR, USD_per_RAI), 
    'error_star_integral': InitialValue(INITIAL_I_ERROR, USD_Seconds_per_RAI), 

    # Aggregate user states
    'RAI_balance': InitialValue(INITIAL_RAI_RESERVE, RAI),
    'ETH_balance': InitialValue(INITIAL_ETH_RESERVE, ETH),
    'ETH_collateral': InitialValue(INITIAL_ETH_LOCKED, ETH),
    'RAI_debt': InitialValue(INITIAL_RAI_DRAWN, RAI)
}

state_variables = prepare_state(raw_state_variables)
