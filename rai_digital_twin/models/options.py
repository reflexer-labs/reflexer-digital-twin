from enum import Enum

class IntegralType(Enum): # Use for both v1 and v2 models
    DEFAULT = 1 # Calculate the error integral using numerical integration
    LEAKY = 2 # Calculate the error integral using numerical integration, with a per-second leak

class DebtPriceSource(Enum): # Used for v1 model
    DISABLED = 0 # Fix the debt price at the starting value, i.e. no price move at each timestep 
    DEFAULT = 1 # Use a normal continuous random variable from SciPy to determine the next price move
    EXTERNAL = 2 # Use the parameter "price_move", a function that returns the price move at each timestep
    DEBT_MARKET_MODEL = 3 # Use the parameter "price_move", a function that returns the price move at each timestep

class MarketPriceSource(Enum): # Used for v1 model
    DEFAULT = 1 # Calculate the market price based on the historically fitted market model
    EXTERNAL = 2 # Use the parameter "price_move", a function that returns the price move at each timestep
