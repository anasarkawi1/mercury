# Algorithmic reading bot v0.1
# Example usage.
# By Anas Arkawi, 2023.
# This file is an example on how the bot can be used to write a simple algorithm which buys ETH when RSI value is at 30 or below, and sells the entire ETH balance (i.e. whatever was filled in the first trade) when RSI is at or above 70.


# Import libraries
import json
from dotenv import load_dotenv 
import os
import time


# Import own class
import class_data as data


# Acquire environment variables for API credentials
load_dotenv()
# API Credentials
apiKey = os.getenv("API_KEY")
apiSecret = os.getenv("API_SECRET")


# Algo parameters
# Algorithm configuration for RSI thresholds and trade quantity.
algoConfig = {
	'trade': {
		'quantity': 0.05,
		'tradeInProgress': False,
	},
	'RSI': {
		'buyThreshold': 40.0,
		'sellThreshold': 60.0,
	}
}


# Routines

# Format the account information from the class and print it on screen
def printAccInfo(accStatus):
	lastPrice = trader.data.iloc[-1]
	lastPriceIndicators = trader.indicatorData.iloc[-1]
	print(f'Current market: p={lastPrice.loc["close"]}, rsi={lastPriceIndicators.loc["RSI"]}')
	print(f'Current account status: ')
	print(f'USDT Balance: {accStatus["assets"]["USDT"]["free"]}')
	print(f'ETH Balance: {accStatus["assets"]["ETH"]["free"]}')
	print(f'ETH Locked Balance: {accStatus["assets"]["ETH"]["locked"]}')


# The function is given to the main class at initialisation and it gets called every price update.
def callback(trader, lastPrice, lastIndicator):

	rsi = lastIndicator.loc['RSI']

	# Entry
	if rsi <= algoConfig['RSI']['buyThreshold'] and algoConfig['trade']['tradeInProgress'] == False:
		# Check if the account balance is sufficient
		account = trader.exchange.account()
		tradePrice = lastPrice.loc['close'] * algoConfig['trade']['quantity']
		if tradePrice > account['assets']['USDT']['free']:
			print('[INFO] Trade failed, insufficient balance.')
			return
		
		# Sufficient balance, send in order
		entryTrade = trader.buy(quantity=algoConfig['trade']['quantity'])
		print('[INFO] Trade entered successfully.')
		print('[INFO] Trade Information:')
		for fill in entryTrade['fills']:
			print(f'Price: {fill["price"]}, Quantity: {fill["qty"]}.')
		algoConfig['trade']['tradeInProgress'] = True
		account = trader.exchange.account()
		printAccInfo(accStatus=account)

	# Exit
	if rsi >= algoConfig['RSI']['sellThreshold'] and algoConfig['trade']['tradeInProgress'] == True:
		account = trader.exchange.account()
		exitTrade = trader.sell(quantity=account["assets"]["ETH"]["free"])
		print('[INFO] Trade exited successfully.')
		print('[INFO] Trade Information:')
		for fill in exitTrade['fills']:
			print(f'Price: {fill["price"]}, Quantity: {fill["qty"]}')
		algoConfig['trade']['tradeInProgress'] == False
		account = trader.exchange.account()
		printAccInfo(account=account)
	


# Define trading object and initialise it.
# The definition of the trading object is done by making an instance of the DataReq class with the target chart settings (i.e. the asset to be traded, chart interval, exchange, etc.) 
trader = data.DataReq(mode='test', tradingPair='ETHUSDT', interval='1m', limit=30, exchange='binance', credentials=[apiKey, apiSecret], updateCallback=callback)

trader.initialise()


# Print current account status at start
printAccInfo(accStatus=trader.exchange.account())