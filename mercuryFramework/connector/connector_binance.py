# Connector library for Binance Public API.
# By Anas Arkawi, 2023.


# Import libraries
from binance.spot import Spot
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient as WebSocketClient
import pandas as pd
from pandas import DataFrame, concat
import numpy as np
import json


# Notes:
#   The classes take in a wsHandler function that handles web socket messages of a given topic that was subscribed. The wsHandler function should be standardised in that it should output a certain array usign


# Class definition
# Arguments:
#   mode: can be 'live' or 'test' and determines if live servers or test servesr should be used,
#   tradingPair: denotes the symbol to be traded,
#   interval: candlestick period,
#   limit: number of past candles that should be obtained.

def spotMode(credentials, baseURL):
    if credentials == None:
        return Spot(base_url=baseURL)
    else:
        return Spot(api_key=credentials[0], api_secret=credentials[1], base_url=baseURL)

class Binance:
    def __init__(self, mode='live', tradingPair=None, interval=None, limit=75, credentials=["", ""], columns=None, wshandler=None):
        if mode == 'live':
            baseURL = 'https://api.binance.com'
            baseWsURL = 'wss://stream.binance.com:9443'
        elif mode == 'test':
            baseURL = 'https://testnet.binance.vision'
            baseWsURL = 'wss://testnet.binance.vision'
        # Connect the spot and websocket clients
        self.clients = {
            "spot": spotMode(credentials=credentials, baseURL=baseURL),
            "ws": WebSocketClient(on_message=self.wsHandlerInternal, stream_url=baseWsURL),
        }
        self.options = {
            "tradingPair": tradingPair,
            "interval": interval,
            "limit": limit,
            "mode": mode,
            "handler": wshandler,
            "columns": columns,
            "dataHandler": wshandler
        }
        self.orderCancellAllowStatus = ['NEW', 'PENDING_NEW', 'PARTIALLY_FILLED']

    def stop(self):
        self.clients['ws'].stop()
    
    # Account endpoint. Used both for general account info and assests in hold
    # TODO: Format the output
    # https://binance-connector.readthedocs.io/en/latest/binance.spot.trade.html#account-information-user-data
    # The balance feature is only available for certain coins for development purposes
    accountData = {
        "commissions": {
            "maker": None,
            "taker": None,
            "buyer": None,
            "seller": None,
        },

        "properties": {
            "status": {
                "trade": None,
                "deposit": None,
                "withdraw": None,
            },
            "type": "SPOT",
        },

        "assets": {
            "BTC": {
                "free": 0.00,
                "locked": 0.00,
            },
            "ETH": {
                "free": 0.00,
                "locked": 0.00,
            },
            "XRP": {
                "free": 0.00,
                "locked": 0.00,
            },
            "USDT": {
                "free": 0.00,
                "locked": 0.00,
            },
        },
    }
    targetAssets = ["BTC", "ETH", "XRP", "USDT"]
    def account(self):
        info = self.clients["spot"].account()

        # Extract price info
        # Extract balance information
        assetsDataFrame = DataFrame(data=info["balances"])
        for name in self.targetAssets:
            currentAsset = assetsDataFrame.loc[assetsDataFrame['asset'] == name]
            self.accountData['assets'][name]['free'] = float(currentAsset['free'].values[0])
            self.accountData['assets'][name]['locked'] = float(currentAsset['locked'].values[0])

        # Extract commision rates
        self.accountData['commissions']['maker'] = float(info['commissionRates']['maker'])
        self.accountData['commissions']['taker'] = float(info['commissionRates']['taker'])
        self.accountData['commissions']['buyer'] = float(info['commissionRates']['buyer'])
        self.accountData['commissions']['seller'] = float(info['commissionRates']['seller'])

        # Extract account properties
        self.accountData['properties']['status']['trade'] = float(info['canTrade'])
        self.accountData['properties']['status']['deposit'] = float(info['canDeposit'])
        self.accountData['properties']['status']['withdraw'] = float(info['canWithdraw'])

        return self.accountData
    
    def profit(self):
        pass

    def apiRestrictions(self):
        pass


    # Market order functions
    def buy(self, quantity):
        result = self.clients["spot"].new_order(symbol=self.options["tradingPair"], side="BUY", type="MARKET", quantity=quantity)
        return result
    
    def sell(self, quantity):
        result = self.clients["spot"].new_order(symbol=self.options["tradingPair"], side="SELL", type="MARKET", quantity=quantity)
        return result
    
    # Limit order functions
    def buyLimit(self, quantity, price):
        result = self.clients["spot"].new_order(
            symbol=self.options["tradingPair"],
            side="BUY",
            type="LIMIT",
            timeInForce="GTC",
            price=price,
            quantity=quantity,
            recvWindow=20000)
        return result

    def sellLimit(self, quantity, price):
        result = self.clients["spot"].new_order(
            symbol=self.options["tradingPair"],
            side="SELL",
            type="LIMIT",
            timeInForce="GTC",
            price=price,
            quantity=quantity)
        return result
    
    
    # Order managment functions

    def queryOrder(self, orderId):
        result = self.clients['spot'].get_order(symbol=self.options['tradingPair'], orderId=orderId)
        return result


    def cancelOrder(self, orderId):
        result = None
        # First check if the order is filled
        query = self.queryOrder(orderId=orderId)
        if query['status'] not in self.orderCancellAllowStatus:
            result = {
                'msg': 'ALREADY_CANCELLED_OR_NXORDER'
            }
        else:
            result = self.clients['spot'].cancel_order(symbol=self.options['tradingPair'], orderId=orderId)
        return result    

    def currentOrder(self):
        result = self.clients['spot'].get_open_orders(symbol=self.options['tradingPair'])
        return result

    def getAllOrders(self):
        result = self.clients['spot'].get_orders(symbol=self.options['tradingPair'])
        return result


    # Data functions

    # The historic data function.
    # Obtains the historic KLine data and formats it into a pandas DataFrame with given columns name.
    # The function for each exchange has to have its own implementation due to their specific output formats.
    def historicData(self):
        kLine = self.clients["spot"].klines(symbol=self.options["tradingPair"], interval=self.options["interval"], limit=self.options["limit"])

        # Column names
        columns = self.options["columns"]

        # Core columns
        coreColumns = ["openTime", "open", "high", "low", "close", "closeTime", "volume", "pChange"]

        # Column data made into a dictionary to be converted into a pandas DataFrame
        columnsData = {}
        for columnName in coreColumns:
            columnsData[columnName] = []


        # Extract the core information
        for candle in kLine:
            columnsData["openTime"].append(int(candle[0]))
            columnsData["open"].append(float(candle[1]))
            columnsData["high"].append(float(candle[2]))
            columnsData["low"].append(float(candle[3]))
            columnsData["close"].append(float(candle[4]))
            columnsData["volume"].append(float(candle[5]))
            columnsData["closeTime"].append(int(candle[6]))
            columnsData["pChange"].append(np.nan)

        # Turn the data into a pandas DataFrame
        result = DataFrame(data=columnsData)

        # Calculate percentage change
        # Due to the usage of pChange in indicator calculations, it is part of the price DataFrame even though it has to be calculated
        result["pChange"] = (result["close"].pct_change()) * 100


        return result
    
    # Sets a websocket connection and outputs an array with the live price update.
    # ^ Test the callback idea first.
    def initiateLiveData(self):
        # Start the WS connection
        # TODO: URGENT: Should it be here? The initial current candlestick insertion (Is this fixed? Indicator data problem is fixed now)
        self.clients["ws"].kline(symbol=self.options['tradingPair'], interval=self.options["interval"])

    # Call everytime a new WebSocket message from the stream is recieved. Never called outside the class, but from the internal WS client instance.
    # Array format: [openTime, open, high, low, close, closeTime, volume].
    # The neccesarry calculation will be done under class_data.
    def wsHandlerInternal(self, _, msg):
        # Process the msg into JSON
        processed = json.loads(msg)

        # Check if the kline data is processed
        if ('k' in processed) == False:
            print('[INTERNAL] WS Not Processed')
            return
        
        # Extract KLine info
        kline = processed['k']
        klineArr = [int(kline['t']),
                    float(kline['o']),
                    float(kline['h']),
                    float(kline['l']),
                    float(kline['c']),
                    int(kline['T']),
                    float(kline['v']),
                    0.0]
        
        self.options['dataHandler'](data=klineArr, closed=kline['x'])