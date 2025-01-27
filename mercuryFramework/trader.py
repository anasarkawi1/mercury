# Algorithmic trading bot v0.1
# Data request module
# By Anas Arkawi, 2023.


# Import libraries
from binance.spot import Spot
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient as WebSocketClient
import pandas as pd
from pandas import DataFrame, concat
import numpy as np
import json
from dataclasses import dataclass

# Import own library
from . import class_calculation
# from .connector.main import Connector
from hermesConnector import Connector


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Sets pandas disable option
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# Initialise calculation functions
calcFunc = class_calculation.Indicators()


# Data Request class
# Used for the retrieval and update of historical and live price data.
class Trader:
    # Request kline data
    def requestKline(self):
        # Get raw data
        # TO-DO: Prevent access outside of the class. Direct access to this variable could cause errors when a price update occurs.
        # FIX: Mention this in the documentation. There are unusual use cases where direct access would be useful.
        self.data = self.exchange.historicData()


        # Define the columns for the indicators
        self.dataColumnsNames = ['openTime']
        for name in self.indicatorFunctionParameters:
            self.dataColumnsNames.append(name)
        
        for maName in self.movingAverageParams:
            self.dataColumnsNames.append(maName)


        # Define DataFrame for indicator calculations
        self.indicatorData = DataFrame(columns=self.dataColumnsNames, index=range(self.options['limit']))

        # Copy openTime to indicatorData for identification
        self.indicatorData['openTime'] = self.data['openTime']


        # TODO: Automatic calculations are restricted to close price as the source.

        # Automatic indicator calculations
        for label, params in self.indicatorFunctionParameters.items():
            self.indicatorData[label] = self.data['close'].rolling(params['length']).apply(params['callback'])

        # Automatic moving average calculation
        for label, params in self.movingAverageParams.items():
            self.indicatorData[label] = self.data['close'].rolling(params['length']).mean()


    # Live price updater.
    # New data processing and calculation of its indicators are done here
    # Data format -> data = [openTime, open, high, low, close, closeTime, volume]
    def dataHandler(self, data, closed):
        # Update price
        # Calculation of pChange is done before insertion since it's used in indicator calculations
        data[-1] = calcFunc.pChange(new=data[4], old=self.data['close'][len(self.data) - 2])

        # Insert new data
        self.data.loc[len(self.data) - 1] = data


        # TODO: I feel like there should be anohter check here (current open == update open?)
        self.indicatorData.iloc[-1, self.indicatorData.columns.get_loc('openTime')] = data[0]


        # Automated indicator calculations
        for label, params in self.indicatorFunctionParameters.items():
            indicatorLen = params['length']
            dataPoints = self.data.iloc[-indicatorLen:, self.data.columns.get_loc('close')]
            self.data.iloc[-1, self.indicatorData.columns.get_loc(label)] = params['callback'](dataPoints)


        # Automated moving average calculations
        for label, params in self.movingAverageParams.items():
            maLen = params['length'];
            self.indicatorData.iloc[-1, self.indicatorData.columns.get_loc(label)] = np.mean(self.data['close'][-maLen:])


        # Check if candlestick is closed, if so, shift prices.
        # implement for indicator data
        if closed:
            self.data.drop(inplace=True, index=0)
            self.data.reset_index(inplace=True)
            self.data.drop(inplace=True, axis=1, columns='index')
            self.data.loc[len(self.data)] = [np.nan for x in range(len(data))]

            self.indicatorData.drop(inplace=True, index=0)
            self.indicatorData.reset_index(inplace=True)
            self.indicatorData.drop(inplace=True, axis=1, columns='index')
            self.indicatorData.loc[len(self.indicatorData)] = [np.nan for x in range(len(self.indicatorData.columns))]

            self.updateCallback(self, self.data.iloc[-1], self.indicatorData.iloc[-1])
            return

        # Return update to original instance
        self.updateCallback(self, self.data.iloc[-1], self.indicatorData.iloc[-1])

    

    # Initialize data frame
    def initialise(self, priceLevel=True):
        # Request for data and format it into a pandas dataframe
        self.requestKline()

        # Initiate live data if requested
        if self.updateCallback != None:
            # Initialise WebSocket client
            self.exchange.initiateLiveData()


    # Deletes the instance
    def delete(self):
        self.exchange.stop()
        self = None


    # Instance initialization
    # TODO: Improve initialisation of `self` values. The value definitions are messy and naming convention is confusing.
    def __init__(
            self,
            mode,
            tradingPair,
            interval,
            credentials,
            limit=150,
            exchange=None,
            updateCallback=None):
        # Define options for the trader instance
        self.options = {
            'tradingPair': tradingPair,
            'interval': interval,
            'limit': limit,
        }

        # Price update callback
        self.updateCallback = updateCallback

        # Indicators and their parameters
        self.indicatorFunctionParameters = {
            "STOCHASTIC": {
                "length": 14,
                "callback": calcFunc.stochasticNew,
                "args": {},
            }
        }

        # Moving average parameters
        self.movingAverageParams = {
            "SMA10": {
                "length": 10,
                "args": {},
            },
            "SMA20": {
                "length": 20,
                "args": {},
            },
            "SMA50": {
                "length": 50,
                "args": {},
            },
        }


        # The connector class returns the specific exchange abstraction class.
        # TODO: Implement error handling
        self.exchange = Connector(
            exchange=exchange,
            credentials=credentials,
            options={
                "mode": mode,
                "tradingPair": tradingPair,
                "interval": interval,
                "limit": limit,
                "columns": None,
                "dataHandler": self.dataHandler if self.updateCallback != None else None,
            }).exchange
        try:
            pass
        except:
            print("FAILED TO INITIALISE EXCHANGE")


    # Order functions
    # TODO: The output coming from the Connector library isn't standardised. Since there's only one supported exchange it's not a huge deal.

    def buy(self, quantity):
        response = self.exchange.buy(quantity=quantity)
        return response
    
    def costBuy(self, cost):
        response = self.exchange.costBuy(cost=cost)
        return response

    def sell(self, quantity):
        response = self.exchange.sell(quantity=quantity)
        return response
    
    def costSell(self, cost):
        response = self.exchange.costSell(cost=cost)
        return response