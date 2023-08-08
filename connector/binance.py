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
class Binance:
    def __init__(self, mode='live', tradingPair=None, interval=None, limit=75, wshandler=None, credentials=[None, None]):
        # Connect the spot and websocket clients
        self.clients = {
            "spot": Spot(api_key=credentials[0], api_secret=credentials[1]),
            "ws": WebSocketClient(on_message=wshandler),
        }
    
    def snapshot():
        pass

    def assets():
        pass