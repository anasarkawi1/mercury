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

# Import own library
import class_calculation


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Sets pandas disable option
pd.set_option('display.float_format', lambda x: '%.3f' % x)



# Initialise calculation functions
calcFunc = class_calculation.Indicators()

# TODO: Fix function return values
# TODO: Make the DataFrame length a constant


# Data
class DataReq:
    # Request kline data
    # Data format: [open time, open price, high price, low price, close price, volume, close time, quote asset volume, number of trades, taker buy base asset volume, taker buy quote asset volume, unused]
    def requestKline(self):
        # Get raw data
        self.rawData = self.client.klines(symbol=self.options["tradingPair"], interval=self.options["interval"], limit=self.options["limit"])

        columns = self.dataColumns
        for price in self.rawData:
            # Insert data into DataFrame
            columns['openTime'].append(float(price[0]))
            columns['open'].append(float(price[1]))
            columns['high'].append(float(price[2]))
            columns['low'].append(float(price[3]))
            columns['close'].append(float(price[4]))
            columns['closeTime'].append(float(price[6]))
            columns['volume'].append(float(price[5]))

        # Insert NaN for data yet to be calculated
        columns['pChange'] = np.nan
        columns['rsi'] = np.nan
        columns['stochastic'] = np.nan
        columns['ma5'] = np.nan

        self.data = DataFrame(data=columns)

        # TODO: Optimise indicator calculations by implementing a single loop system

        # Calculate percentage change
        # TODO: Uses manual iteration, optimize for faster results. (pandas.DataFrame.apply?)
        pVals = [np.nan]
        for i in range(0, len(self.data) - 1):
            pVals.append(calcFunc.pChange(self.data['close'][i + 1], self.data['close'][i]))
        self.data['pChange'] = pVals
        

        # Calculate RSI
        rsiLength = 14
        rsiLength = rsiLength - 1 # Accounts for the index start being set to 0
        for i in range(rsiLength, len(self.data) - 1):
            prices = self.data['pChange'][i - rsiLength : i].to_numpy()
            rsi = calcFunc.rsi(prices=prices)
            self.data['rsi'][i] = rsi
        
        # Calculate Stochastic
        stochasticLength = 14
        stochasticLength = stochasticLength - 1 # Accounts for the index start being set to 0
        for i in range(stochasticLength, len(self.data) - 1):
            prices = self.data['pChange'][i - stochasticLength : i].to_numpy()
            stochastic = calcFunc.stochastic(prices=prices)
            self.data['stochastic'][i] = stochastic

        # TODO: Implement a system for the automatic addition of moving averages

        # Calculate moving average (length = 21)
        avgArr = []
        maLen = 5
        maLen = maLen - 1 # Accounts for the index start being set to 0
        for i in range(maLen, (len(self.data) - 1) ):
            prices = self.data['close'][i - maLen : i].to_numpy()
            avg = calcFunc.avg(prices=prices)
            self.data['ma5'][i] = avg

        # Drop NaN should only be used when all initial calculations have been done.
        # self.data = self.data.dropna()

    # Live price updater.
    def wsHandler(self, _, msg):
        # Process WebSocket message from string to python dictionary
        processed = json.loads(msg)

        # Check if the message contains KLine information
        if ('k' in processed) == False:
            return
        
        # Extract KLine info
        kline = processed['k']

        # Convert dict into suitable array
        # [openTime, open, high, low, close, closeTime, volume, pChange.}
        # TODO: Standardise declerations.
        # TODO: Automate addition of moving averages and insert them at the end of the columns (?)
        klineArr = [
            int(kline['t']),
            float(kline['o']),
            float(kline['h']),
            float(kline['l']),
            float(kline['c']),
            int(kline['T']),
            float(kline['v']),
            calcFunc.pChange(self.data['close'][len(self.data) - 1],
            float(kline['c'])),
            calcFunc.rsi(prices=self.data['pChange'][ (len(self.data['pChange']) - 14) : (len(self.data['pChange'] - 2)) ].to_numpy() ), # RSI
            calcFunc.stochastic(prices=self.data['pChange'][ (len(self.data['pChange']) - 14) : (len(self.data['pChange'] - 2)) ].to_numpy() ), # Stochastic
            calcFunc.avg(prices=self.data['close'][ (len(self.data['close']) - 21) : (len(self.data['close'] - 1))] )
            ]

        # Update new price
        self.data.loc[len(self.data) - 1] = klineArr
        
        
        # Check if the candlestick is closed, if so shift prices
        if kline['x']:
            self.data.drop(inplace=True, index=0)
            self.data.reset_index(inplace=True)
            self.data.drop(inplace=True, axis=1, columns='index')
            self.data.loc[len(self.data)] = [np.nan for x in range(len(klineArr))]

        print(self.data)

    # Initialize data frame
    def initialise(self, priceLevel=True):
        # Request for data and format it into a pandas dataframe
        self.requestKline()
        print(self.data)
        print('Kline data has been recieved. Initialising WebSocket connection...')

        # Initialise WebSocket client
        self.wsClient.kline(symbol=self.options['tradingPair'], interval=self.options['interval'])

    # Instance initialization
    def __init__(self, tradingPair, interval, limit):
        # Define options for the trader instance
        self.options = {
            'tradingPair': tradingPair,
            'interval': interval,
            'limit': limit,
            'threshold': 0.25
        }
        
        # Define Binance clients for the REST API and WebSocket interfaces.
        self.client = Spot()
        self.wsClient = WebSocketClient(on_message=self.wsHandler)

        # Define column names for the pandas DataFrame
        self.dataColumns = {
            'openTime': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'closeTime': [],
            'volume': [],
            'pChange': [],
            'rsi': []
        }

        # Price levels
        # TODO: Implement level and price action calculations
        self.levels = {
            'resistance': DataFrame(data=self.dataColumns),
            'support': DataFrame(data=self.dataColumns)
        }

        # Indicators data
        self.indicatorData = {}
        # Moving average data
        # TODO: Automate moving average calculation by obtaining length values from a global list
        self.indicatorData['movingAvg'] = {}

