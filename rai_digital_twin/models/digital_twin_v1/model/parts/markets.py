import rai_digital_twin.failure_modes as failure


def s_RAI_balance(params, substep, state_history, state, policy_input):
    RAI_balance = state['RAI_balance']
    RAI_delta = policy_input['RAI_delta']
    updated_RAI_balance = RAI_balance + RAI_delta
    if not updated_RAI_balance > 0:
         raise failure.NegativeBalanceException(f'Uniswap RAI {RAI_balance=} {RAI_delta=}')
    else:
        return "RAI_balance", updated_RAI_balance


def s_ETH_balance(params, substep, state_history, state, policy_input):
    ETH_balance = state['ETH_balance']
    ETH_delta = policy_input['ETH_delta']
    updated_ETH_balance = ETH_balance + ETH_delta
    if not updated_ETH_balance > 0:
         raise failure.NegativeBalanceException(f'Uniswap ETH {ETH_balance=} {ETH_delta=}')
    else:
        return "ETH_balance", updated_ETH_balance


def s_market_price_twap(params, substep, state_history, state, policy_input):
    value = 0
    return ("market_price_twap", value)

