class CustomException(Exception):
    def __init__(self, context=""):
        self.name = self.__class__.__name__
        self.context = context
        super(Exception, self).__init__((self.name, self.context))

    def __getstate__(self):
        return (self.name, self.context)
        
    def __setstate__(self, args):
        self.context, self.name = args

class NegativeBalanceException(CustomException):
    pass

class LiquidationRatioException(CustomException):
    pass

class ControllerTargetOverflowException(CustomException):
    pass

class ArbitrageConditionException(CustomException):
    pass

class InvalidCDPStateException(CustomException):
    pass

class InvalidCDPTransactionException(CustomException):
    pass

class InvalidSecondaryMarketDeltaException(CustomException):
    pass

class AssertionError(CustomException):
    pass