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
from .connector.main import Connector


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Sets pandas disable option
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# Initialise calculation functions
calcFunc = class_calculation.Indicators()


# Data Request class
# Used for the retrieval and update of historical and live price data.
# TODO: Fix function return values
# TODO: Make the DataFrame length a constant
class Trader:
    # Request kline data
    # Data format: [open time, open price, high price, low price, close price, volume, close time, quote asset volume, number of trades, taker buy base asset volume, taker buy quote asset volume, unused]
    def requestKline(self):
        # Get raw data
        # TODO: Prevent access outside of the class. Direct access to this variable could cause errors when a price update occurs.
        self.data = self.exchange.historicData()
        # Define DataFrame for indicator calculations
        self.indicatorData = DataFrame(columns=self.dataColumnsNames, index=range(self.options['limit']))

        # Copy openTime to indicatorData for identification
        self.indicatorData['openTime'] = self.data['openTime']


        # TODO: Automatic calculations are restricted to close price as the source.


        # Automatic indicator calculations
        for label, params in self.indicatorFunctionParameters.items():
            self.indicatorData[label] = self.data['close'].rolling(params['length']).apply(params['callback'])

        # # Indicator calculations
        # # Calculate RSI
        # rsiLength = 14
        # self.indicatorData['RSI'] = self.data['close'].rolling(rsiLength).apply(calcFunc.rsiNew)
        # 
        # # Calculate Stochastic
        # stochasticLength = 14
        # self.indicatorData['STOCHASTIC'] = self.data['close'].rolling(stochasticLength).apply(calcFunc.stochasticNew)


        # Automatic moving average calculation
        for label, params in self.movingAverageParams.items():
            print(params)
            self.indicatorData[label] = self.data['close'].rolling(params['length']).mean()


    # Live price updater.
    # New data processing and calculation of its indicators are done here
    # Data format -> data = [openTime, open, high, low, close, closeTime, volume]
    def dataHandler(self, data, closed):
        # Update price
        # Calculation of pChange is done before insertion since it's used in indicator calculations
        data[-1] = calcFunc.pChange(new=data[4], old=self.data['close'][len(self.data) - 2])
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
        # TODO: URGENT: The drop happens and the index gets shifted which causes a race condition that throws and exception
        # TODO: This issue still persists?? Possible solution: Call the external callback when the functions of the if statement gets done.
        if closed:
            self.data.drop(inplace=True, index=0)
            self.data.reset_index(inplace=True)
            self.data.drop(inplace=True, axis=1, columns='index')
            self.data.loc[len(self.data)] = [np.nan for x in range(len(data))]

            self.indicatorData.drop(inplace=True, index=0)
            self.indicatorData.reset_index(inplace=True)
            self.indicatorData.drop(inplace=True, axis=1, columns='index')
            self.indicatorData.loc[len(self.indicatorData)] = [np.nan for x in range(len(self.indicatorData.columns))]

        # Return update to original instance
        self.updateCallback(self, self.data.iloc[-1], self.indicatorData.iloc[-1])

    

    # Initialize data frame
    def initialise(self, priceLevel=True):
        # Request for data and format it into a pandas dataframe
        self.requestKline()
        print('Kline data has been recieved. Initialising WebSocket connection...')

        # Initialise WebSocket client
        self.exchange.initiateLiveData()


    # Deletes the instance
    def delete(self):
        self.exchange.stop()
        self = None

    # Instance initialization
    # TODO: Improve initialisation of `self` values. The value definitions are messy and naming convention is confusing.
    def __init__(self, mode, tradingPair, interval, credentials, limit=150, exchange=None, updateCallback=None):
        # Define options for the trader instance
        self.options = {
            'tradingPair': tradingPair,
            'interval': interval,
            'limit': limit,
            # 'threshold': 0.25
        }

        self.updateCallback = updateCallback

        # Define column names for the pandas DataFrame
        # The addition of indicators are done through the below array. A configuration file should be used to define the below information.
        # TODO: URGENT: These should be derived from indicatorsParameterData. Right now I'm working on the backend of lycon so this is secondary.
        self.dataColumnsNames = ["openTime", "RSI", "STOCHASTIC", "SMA10", "SMA20", "SMA50"]
        self.dataColumns = {
            'openTime': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'closeTime': [],
            'volume': [],
            'pChange': [],
            'RSI': []
        }

        # Indicators data
        # TODO: (issue: #2), seperate indicator parameters from the main code and load them dynamically.
        self.indicatorFunctionParameters = {
            "RSI": {
                "length": 14,
                "callback": calcFunc.rsiNew,
                "args": {},
            },
            "STOCHASTIC": {
                "length": 14,
                "callback": calcFunc.stochasticNew,
                "args": {},
            }
        }
        self.movingAverageParams = {
            "SMA10": {
                "length": 10,
                "callback": None,
                "args": {},
            },
            "SMA20": {
                "length": 20,
                "callback": None,
                "args": {},
            },
            "SMA50": {
                "length": 50,
                "callback": None,
                "args": {},
            },
        }


        # The connector class determines the specific exchange standardisation class according to the exchange parameter and returns it.
        # TODO: Implement error handling
        self.exchange = Connector(exchange=exchange, credentials=credentials, options={
                "mode": mode,
                "tradingPair": tradingPair,
                "interval": interval,
                "limit": limit,
                "columns": self.dataColumnsNames,
                "dataHandler": self.dataHandler,
            }).exchange
        try:
            pass
        except:
            print("FAILED TO INITIALISE EXCHANGE")

        # Algo variables
        self.algo = None
        self.tradeInProgress = False


    def buy(self, quantity):
        response = self.exchange.buy(quantity=quantity)
        return response

    def sell(self, quantity):
        response = self.exchange.sell(quantity=quantity)
        return response
    
    
    # Algorithm functions

    @dataclass
    class AlgoDefs:
        indicatorStrategy: bool

        # Indicators to be used (if indicatorStrategy is true)
        buyEnabled: list
        sellEnabled: list

        # Change in moving averages to be used (if indicatorStrategy is false.)
        # TODO: How the hell would you implement difference between MAs??
        changeBuy: list
        changeSell: list

        # Trade information
        quantity: float

        # Parameters
        indicators: object # TODO: define the object
        change: object # TODO: same as above



    # Recieves an object with the parameters for the algorithm. Each instance should have a single algorithm.
    def algoCreate(self, algoParams):
        self.algoParams = algoParams

    # Recieves a state for the drunk
    def algoRun():
        pass


    def algoCreateOLD(self, algoParams, id=0):
        # algoParams.quantity = self.exchange.account()["assets"]["USDT"]["free"]
        # self.algo = algoParams
        pass

    # Algorithm function. Runs the user-defined algorithm supplied from self.algo.
    # Current implementation was scrapped, but can be accessed in GitHub Gist. Check issue #5 for more information on the matter.
    def algoRunOLD(self):
        if self.algo == None:
            return False
        return True