# Algorithmic trading bot v0.1
# Data request module
# By Anas Arkawi, 2023.


# Import libraries
import pandas as pd
from pandas import DataFrame
import numpy as np
from typing import Literal, Tuple

from mercuryFramework.mercury_exceptions import GenericMercuryError, InsufficientOrderArgumentsError, OrderSideError, QtyAndNotionalError, TimeInForceError

# Import own library
from . import class_calculation
# from .connector.main import Connector

# Import Hermes and its modules
from hermesConnector import Connector
from hermesConnector.hermes_enums import OrderSide, TimeInForce
from hermesConnector.models import MarketOrderResult, MarketOrderQtyParams, LimitOrderBaseParams, LimitOrderResult
from hermesConnector.timeframe import TimeFrame


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

    # Instance initialization
    # TODO: Improve initialisation of `self` values. The value definitions are messy and naming convention is confusing.
    def __init__(
            self,
            mode: Literal["live", "test"],
            tradingPair: str,
            interval: TimeFrame,
            credentials: Tuple[str, str],
            exchange: str,      # TODO: This should be turned into a proper Enum.
            limit=150,
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
                "dataHandler": (self.dataHandler if self.updateCallback != None else None),
            }).exchange
        try:
            pass
        except:
            print("FAILED TO INITIALISE EXCHANGE")

    # TODO: Should be done?
    # Request kline data
    def requestKline(self):
        # Get raw data
        self.data: DataFrame = self.exchange.historicData()


        # Define the columns for the indicators
        self.dataColumnsNames = ['openTime']
        for name in self.indicatorFunctionParameters:
            self.dataColumnsNames.append(name)
        
        for maName in self.movingAverageParams:
            self.dataColumnsNames.append(maName)


        # Define DataFrame for indicator calculations
        self.indicatorData = DataFrame(columns=self.dataColumnsNames, index=range(len(self.data)))

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
        self.data.iloc[-1] = data


        # TODO: I feel like there should be anohter check here (current open == update open?)
        self.indicatorData.iloc[-1, self.indicatorData.columns.get_loc('openTime')] = data[0]


        # Automated indicator calculations
        for label, params in self.indicatorFunctionParameters.items():
            indicatorLen = params['length']
            dataPoints = self.data.iloc[-indicatorLen:, self.data.columns.get_loc('close')]
            self.data.iloc[-1, self.indicatorData.columns.get_loc(label)] = params['callback'](dataPoints)


        # Automated moving average calculations
        for label, params in self.movingAverageParams.items():
            maLen = params['length']
            maVal = np.mean(self.data['close'][-maLen:])
            self.indicatorData[label].iloc[-1] = maVal


        # Check if candlestick is closed, if so, shift prices.
        # implement for indicator data
        if closed:
            self.data.drop(inplace=True, index=0)
            self.data.reset_index(inplace=True)
            self.data.drop(inplace=True, axis=1, columns='index')
            self.data.loc[len(self.data)] = [np.nan for x in range(len(data))] # type: ignore

            self.indicatorData.drop(inplace=True, index=0)
            self.indicatorData.reset_index(inplace=True)
            self.indicatorData.drop(inplace=True, axis=1, columns='index')
            self.indicatorData.loc[len(self.indicatorData)] = [np.nan for x in range(len(self.indicatorData.columns))] # type: ignore

            if (self.updateCallback != None):
                self.updateCallback(
                    self,
                    self.data.iloc[-1],
                    self.indicatorData.iloc[-1])
            return

        # Return update to original instance
        if (self.updateCallback != None):
            self.updateCallback(
                self,
                self.data.iloc[-1],
                self.indicatorData.iloc[-1])

    
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


    # Order functions

    def marketOrder(
            self,
            side: OrderSide,
            qty=None,
            notional=None,
            tif=TimeInForce.DAY
    ) -> MarketOrderResult:
        
        # Check if too many arguments were supplied
        if (
            (qty        != None) and
            (notional   != None)
        ):
            raise QtyAndNotionalError
        
        # Check if no arguments were supplied
        if (
            (qty == None) and
            (notional == None)
        ):
            raise InsufficientOrderArgumentsError
        
        # Check if the price information are supplied properly
        if (qty != None):
            if (qty <= 0):
                raise InsufficientOrderArgumentsError
        elif (notional != None):
            if (notional <= 0):
                raise InsufficientOrderArgumentsError

        # Check if order side was supplied
        if (isinstance(side, OrderSide) == False):
            raise OrderSideError
        
        # Check if time in force parameter was supplied
        if (isinstance(tif, TimeInForce) == False):
            raise TimeInForceError
        
        # Submit order
        orderResult = None
        if (qty != None):
            req = MarketOrderQtyParams(
                side=side,
                tif=tif,
                qty=qty)
            orderResult = self.exchange.marketOrderQty(req)

        # If the submit method fails it will just throw an error. If a None is returned, its an undefined edge case.
        if (orderResult == None):
            raise GenericMercuryError
        
        return orderResult
    

    def limitOrder(
            self,
            side: OrderSide,
            limitPrice,
            qty=None,
            tif=TimeInForce.DAY
    ) -> LimitOrderResult:
        
        # Check if no arguments were supplied
        if (
            (qty == None) or
            (limitPrice == None)):
            raise InsufficientOrderArgumentsError
        
        # Check if the price information are supplied properly
        if (
            (qty <= 0) or
            (limitPrice <= 0)):
            raise InsufficientOrderArgumentsError
        
        # Check if all the arguments were supplied was supplied
        if (isinstance(side, OrderSide) == False):
            raise OrderSideError
        
        if (isinstance(tif, TimeInForce) == False):
            raise TimeInForceError
        
        # Submit order
        orderResult = None
        if (qty != None):
            req = LimitOrderBaseParams(
                side=side,
                limitPrice=limitPrice,
                qty=qty,
                tif=tif
            )
            orderResult = self.exchange.limitOrder(req)

        # If the submit method fails it will just throw an error. If a None is returned, its an undefined edge case.
        if (orderResult == None):
            raise GenericMercuryError
        
        return orderResult

