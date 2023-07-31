# Algorithmic trading bot v0.1
# Calculation module. Contains classes for calculating certain indicators price levels, etc.
# By Anas Arkawi, 2023.

import numpy as np

# Technical indicators
class Indicators:
    def pChange(self, old, new):
        pChange = new - old
        pChange = pChange / old
        pChange = pChange * 100
        return pChange
    
    # RSI Calculation
    # TODO: Improve calculations by reducing operations
    def rsi(self, prices):
        rsi = 0
        # Average gain calculation
        avgG = 0
        avgL = 0
        for i in range(len(prices) - 1):
            currentChange = prices[i + 1] - prices[i]
            if currentChange > 0:
                avgG += currentChange
            elif currentChange < 0:
                avgL += np.absolute(currentChange)
        avgG = avgG/14
        avgL = avgL/14

        # RSI Calculation first part
        if avgL == 0:
            return 0
        rsi = 1 + (avgG/avgL)
        rsi = 100 / rsi
        rsi = 100 - rsi
        return rsi

    def stochastic(self, prices):
        cMax = np.max(prices)
        cMin = np.min(prices)

        val = cMax - cMin
        val = ((prices[len(prices) - 1]) - cMin) / val
        val = 100 * val

        return val

    def macd(self, prices):
        pass
    
    # Moving average calculations
    # TODO: A system has to be implemented for moving averages specifically due to their high flexibility. A similar system should be implemented for EMAs they're being implemented.
    def avg(self, prices):
        average = 0
        for price in prices:
            average += price
        average = average / len(prices)
        return average

# TODO: Implement level and price action calculations
class PriceLevel:
    pass