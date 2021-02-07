import models.system_model_v3.model.parts.failure_modes as failure


def update_RAI_balance(params, substep, state_history, state, policy_input):
    RAI_balance = state['RAI_balance']
    RAI_delta = policy_input['RAI_delta']
    updated_RAI_balance = RAI_balance + RAI_delta
    if not updated_RAI_balance > 0: raise failure.NegativeBalanceException('Uniswap RAI')
    return "RAI_balance", updated_RAI_balance

def update_ETH_balance(params, substep, state_history, state, policy_input):
    ETH_balance = state['ETH_balance']
    ETH_delta = policy_input['ETH_delta']
    updated_ETH_balance = ETH_balance + ETH_delta
    if not updated_ETH_balance > 0: raise failure.NegativeBalanceException('Uniswap ETH')
    return "ETH_balance", updated_ETH_balance

def update_UNI_supply(params, substep, state_history, state, policy_input):
    UNI_supply = state['UNI_supply']
    UNI_delta = policy_input['UNI_delta']
    updated_UNI_supply = UNI_supply + UNI_delta
    if not updated_UNI_supply > 0: raise failure.NegativeBalanceException('Uniswap UNI')
    return "UNI_supply", updated_UNI_supply

# Uniswap functions
# See https://github.com/runtimeverification/verified-smart-contracts/blob/uniswap/uniswap/x-y-k.pdf for original v1 specification

def add_liquidity(reserve_balance, supply_balance, voucher_balance, tokens, value):
    '''
    Example:
    new_reserve = (1 + alpha)*reserve_balance
    new_supply = (1 + alpha)*supply_balance
    new_vouchers = (1 + alpha)*voucher_balance
    '''
    if voucher_balance <= 0:        
        dr = value
        ds = tokens
        dv = tokens
        return (dr, ds, dv)
    
    alpha = value/reserve_balance
    
    dr = alpha*reserve_balance
    ds = alpha*supply_balance
    dv = alpha*voucher_balance
    
    return (dr, ds, dv)

def remove_liquidity(reserve_balance, supply_balance, voucher_balance, tokens):
    '''
    Example:
    new_reserve = (1 - alpha)*reserve_balance
    new_supply = (1 - alpha)*supply_balance
    new_liquidity_tokens = (1 - alpha)*liquidity_token_balance
    '''
    alpha = tokens/voucher_balance
    
    dr = -alpha*reserve_balance
    ds = -alpha*supply_balance
    dv = -alpha*voucher_balance
    
    return (dr, ds, dv)

def get_input_price(dx, x_balance, y_balance, trade_fee=0.01):
    '''
    How much y received for selling dx?

    Example:
    new_x = (1 + alpha)*x_balance
    new_y = y_balance - dy
    '''
    rho = trade_fee
    
    alpha = dx / x_balance
    gamma = 1 - rho
    
    dy = (alpha * gamma / (1 + alpha * gamma)) * y_balance
    
    _dx = alpha * x_balance
    _dy = -dy
    
    return (_dx, _dy)

def get_output_price(dy, x_balance, y_balance, trade_fee=0.01):
    '''
    How much x needs to be sold to buy dy?

    Example:
    new_x = x_balance + dx
    new_y = (1 - beta)*y_balance
    '''
    rho = trade_fee
    
    beta = dy / y_balance
    gamma = 1 - rho
    
    dx = (beta / (1 - beta)) * (1 / gamma) * x_balance
    
    _dx = dx
    _dy = -beta * y_balance
    
    return (_dx, _dy)

# Token trading
def collateral_to_token(value, reserve_balance, supply_balance, trade_fee):
    '''
    Trade collateral for token

    Example:
    new_reserve = reserve_balance + dx
    new_supply = supply_balance - dy
    '''
    if reserve_balance == 0: return 0
    dx,dy = get_input_price(value, reserve_balance, supply_balance, trade_fee)
    
    return abs(dy)

def token_to_collateral(tokens, reserve_balance, supply_balance, trade_fee):
    '''
    Trade token for collateral

    Example:
    new_reserve = reserve_balance - dx
    new_supply = supply_balance + dy
    '''
    if supply_balance == 0: return 0
    dx,dy = get_input_price(tokens, supply_balance, reserve_balance, trade_fee)
    
    return abs(dy)
