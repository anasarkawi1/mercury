# Algorithmic reading bot v0.1
# Main bot
# By Anas Arkawi, 2023.
#
# This version of the bot is going to be the foundation for all future versions. This version includes all the necessary class definitions and structures that allow it to be expandable and built upon with ease allowing for more freedom when working on the financial side.


# Example usage file


# Import libraries
import json


# Import own class
import class_data as data



# Define trading object
trader = data.DataReq(mode='live', tradingPair='ETHUSDT', interval='1m', limit=30, exchange='binance', credentials=None)

# initialise trader
trader.initialise()


# Algo config
algoConfig = {
	'RSI': {
		'threshold': 30
	}
}


# Runtime functions 
def getAccInfo():
	acc = json.dumps(trader.exchange.account())
	return acc


# Algo
while True == False:
	lastPrice = trader.data.iloc[-1]
	lastPriceIndicators = trader.indicatorData.iloc[-1]

	rsi = lastPriceIndicators.loc['RSI']
	if rsi <= algoConfig['RSI']['threshold']:
		print('[INFO] Trade Executed, RSI threshold reached')
		trader.buy(quantity=5)
		print(getAccInfo())
