from models.system_model_v3.model.state_variables.historical_state import target_price, eth_price

uniswap_rai_balance = 5e6
uniswap_eth_balance = (5e6 * target_price) / eth_price
