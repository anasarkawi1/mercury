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


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Sets pandas disable option
pd.set_option('display.float_format', lambda x: '%.3f' % x)


# TODO: Fix function return values


# Data
class DataReq:
    # Indicators calculation functions
    # TODO: Seperate these functions into "class_calculation.py" file
    # Calculate percentage change
    def pChangeFunc(self, old, new):
        pChange = new - old
        pChange = pChange / old
        pChange = pChange * 100
        return pChange
    
    # Moving average
    # TODO: A system has to be implemented for moving averages specifically due to their high flexibility. A similar system should be implemented for EMAs they're being implemented.
    def movingAvg(self, prices):
        average = 0
        for price in prices:
            average += price['close']
        average = average / len(prices)
        return average

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
        columns['ma5'] = np.nan

        self.data = DataFrame(data=columns)

        # Calculate percentage change
        # TODO: Uses manual iteration, optimize for faster results. (pandas.DataFrame.apply?)
        pVals = [np.nan]
        for i in range(0, len(self.data) - 1):
            pVals.append(self.pChangeFunc(self.data['close'][i + 1], self.data['close'][i]))
        self.data['pChange'] = pVals

        # Calculate moving average (length = 5)
        avgArr = []
        maLen = 5
        for i in range(0, len(self.data) - 1):
            if len(avgArr) != maLen:
                avgArr.append(self.data['close'][i])
            else:
                avg = np.sum(avgArr)
                avg = avg / maLen
                # self.data.loc[price['openTime']]['ma5'] = avg
                self.data['ma5'][i] = avg
                avgArr.append(self.data['close'][i])
                avgArr.pop(0)


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
        klineArr = [
            int(kline['t']),
            float(kline['o']),
            float(kline['h']),
            float(kline['l']),
            float(kline['c']),
            int(kline['T']),
            float(kline['v']),
            self.pChangeFunc(self.data['close'][len(self.data) - 1],
            float(kline['c'])),
            np.nan,
            np.nan
            ]

        # Update new price
        self.data.loc[len(self.data) - 1] = klineArr

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
            'resistance': [],
            'support': DataFrame(data=self.dataColumns)
        }

