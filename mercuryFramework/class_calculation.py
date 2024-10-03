# Algorithmic trading bot v0.1
# Calculation module. Contains classes for calculating certain indicators price levels, etc.
# By Anas Arkawi, 2023.

import numpy as np


# Technical indicators
class Indicators:
    def pChange(self, old, new):
        pChange = (new - old) / old
        return pChange * 100
    
    # RSI Calculation
    # TODO: Implement second part of RSI
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
    
    def rsiNew(self, prices):
        length = len(prices)
        diff = np.diff(prices)

        gains = diff[diff > 0]
        avgGain = np.sum(gains) / length

        losses = np.abs(diff[diff < 0])
        avgLoss = np.sum(losses) / length

        rs = avgGain/avgLoss
        rsiVal = 100/(1+rs)
        rsiVal = 100 - rsiVal

        return rsiVal

    def stochastic(self, prices):
        cMax = np.max(prices)
        cMin = np.min(prices)

        val = cMax - cMin
        # Check if val = 0
        if val != 0:
            val = ((prices[len(prices) - 1]) - cMin) / val
        val = 100 * val

        return val
    
    def stochasticNew(self, prices):
        # For the calculation of the stochastic indicator we need,
        #   - Current close price (i.e. the last value)
        #   - The lowest price in the range
        #   - The highest price in the range

        # Retrieve vals
        currentClose = prices.iat[-1]
        lowest = prices.min()
        highest = prices.max()

        # Perform calculations
        val = (currentClose - lowest) / (highest - lowest)
        val = val * 100

        return val

    def macd(self, prices):
        pass


# TODO: Implement level and price action calculations
class PriceLevel:
    pass