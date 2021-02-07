class CustomException(Exception):
    def __init__(self, context=""):
        self.name = self.__class__.__name__
        self.context = context
        super(Exception, self).__init__(self.name, self.context)

    def __getstate__(self):
        return (self.name, self.context)
        
    def __setstate__(self, args):
        self.name, self.context = args

class NegativeBalanceException(CustomException):
    pass

class LiquidationRatioException(CustomException):
    pass

class ControllerTargetOverflowException(CustomException):
    pass

