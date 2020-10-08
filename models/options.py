from enum import Enum

class IntegralType(Enum):
    DEFAULT = 1
    LEAKY = 2

class DebtPriceSource(Enum):
    DISABLED = 0
    DEFAULT = 1
    EXTERNAL = 2
    DEBT_MARKET_MODEL = 3

class MarketPriceSource(Enum):
    DEFAULT = 1
    EXTERNAL = 2
    HYBRID = 3
