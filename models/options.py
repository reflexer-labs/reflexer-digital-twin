from enum import Enum

class IntegralType(Enum):
    DEFAULT = 1
    LEAKY = 2

class DebtPriceSource(Enum):
    DEFAULT = 1
    EXTERNAL = 2
    DEBT_MARKET_MODEL = 3
