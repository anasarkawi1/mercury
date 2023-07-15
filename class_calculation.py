# Algorithmic trading bot v0.1
# Calculation module. Contains classes for calculating certain indicators price levels, etc.
# By Anas Arkawi, 2023.

class Indicators:
    def rsi(self, df):
        pass

    def pChange(self, old, new):
        pChange = new - old
        pChange = pChange / old
        pChange = pChange * 100
        return pChange
    
    # Moving average calculations
    # TODO: A system has to be implemented for moving averages specifically due to their high flexibility. A similar system should be implemented for EMAs they're being implemented.
    def movingAvg(self, prices):
        average = 0
        for price in prices:
            average += price
        average = average / len(prices)
        return average

# TODO: Implement level and price action calculations
class PriceLevel:
    pass