# Algorithmic reading bot v0.1
# Main bot
# By Anas Arkawi, 2023.
#
# This version of the bot is going to be the foundation for all future versions. This version includes all the necessary class definitions and structures that allow it to be expandable and built upon with ease allowing for more freedom when working on the financial side.


# Import libraries
from binance.spot import Spot
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient as WebSocketClient
from flask import Flask
#from pandas import DataFrame
#import numpy as np


# Import own class
import class_data as data


# Define trading object
trader = data.DataReq(tradingPair='ETHUSDT', interval='1h', limit=40)

# initialise trader
trader.initialise()

