def update_RAI_balance(params, substep, state_history, state, policy_input):
    RAI_balance = state['RAI_balance']
    RAI_delta = policy_input['RAI_delta']
    return "RAI_balance", RAI_balance + RAI_delta

def update_ETH_balance(params, substep, state_history, state, policy_input):
    ETH_balance = state['ETH_balance']
    ETH_delta = policy_input['ETH_delta']
    return "ETH_balance", ETH_balance + ETH_delta

def update_UNI_supply(params, substep, state_history, state, policy_input):
    UNI_supply = state['UNI_supply']
    UNI_delta = policy_input['UNI_delta']
    return "UNI_supply", UNI_supply + UNI_delta

# Uniswap functions

def add_liquidity(reserve_balance, supply_balance, voucher_balance, tokens, value):
    if voucher_balance <= 0:        
        dr = value
        ds = tokens
        dv = tokens
        return (dr, ds, dv)
    
    alpha = value/reserve_balance
    
    dr = alpha*reserve_balance
    ds = alpha*supply_balance
    dv = alpha*voucher_balance
    
    #new_reserve = (1 + alpha)*reserve_balance
    #new_supply = (1 + alpha)*supply_balance
    #new_vouchers = (1 + alpha)*voucher_balance
    
    return (dr, ds, dv)

def remove_liquidity(reserve_balance, supply_balance, voucher_balance, tokens):
    alpha = tokens/voucher_balance
    
    dr = -alpha*reserve_balance
    ds = -alpha*supply_balance
    dv = -alpha*voucher_balance
    
    #new_reserve = (1 - alpha)*reserve_balance
    #new_supply = (1 - alpha)*supply_balance
    #new_liquidity_tokens = (1 - alpha)*liquidity_token_balance
    
    return (dr, ds, dv)

# How much y received for selling dx?
def get_input_price(dx, x_balance, y_balance, trade_fee=0.01):
    rho = trade_fee
    
    alpha = dx/x_balance
    gamma = 1 - rho
    
    dy = (alpha*gamma / (1 + alpha*gamma))*y_balance
    
    _dx = alpha*x_balance
    _dy = -dy
    
    #new_x = (1 + alpha)*x_balance
    #new_y = y_balance - dy
    
    return (_dx, _dy)

# How much x needs to be sold to buy dy?
def get_output_price(dy, x_balance, y_balance, trade_fee=0.01):
    rho = trade_fee
    
    beta = dy/y_balance
    gamma = 1 - rho
    
    dx = (beta / (1 - beta))*(1 / gamma)*x_balance
    
    _dx = dx
    _dy = -beta*y_balance
    
    #new_x = x_balance + dx
    #new_y = (1 - beta)*y_balance
    
    return (_dx, _dy)

# Token trading
def collateral_to_token(value, reserve_balance, supply_balance, trade_fee):
    if reserve_balance == 0: return 0
    dx,dy = get_input_price(value, reserve_balance, supply_balance, trade_fee)
    
    #new_reserve = reserve_balance + dx
    #new_supply = supply_balance - dy
    
    return abs(dy)

def token_to_collateral(tokens, reserve_balance, supply_balance, trade_fee):
    if supply_balance == 0: return 0
    dx,dy = get_input_price(tokens, supply_balance, reserve_balance, trade_fee)
    
    #new_reserve = reserve_balance - dx
    #new_supply = supply_balance + dy
    
    return abs(dy)
