import math
from decimal import *
import sys

getcontext().prec = 27

globalRate = sys.argv[1]
duration = sys.argv[2]

redemptionRate = Decimal(globalRate)
timeline = Decimal(duration)
adjustedRR = redemptionRate / Decimal(100) + Decimal(1)
scaledPerSecondRate = Decimal(math.exp(Decimal(math.log(adjustedRR)) / timeline)) * Decimal(10**27)
print(str(scaledPerSecondRate))
sys.stdout.flush()
