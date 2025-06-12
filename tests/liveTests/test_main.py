# Mercury Test Script
# By Anas Arkawi, 2025.


# Import modules
import pytest
from dotenv import load_dotenv
import os
from mercuryFramework.mercury_exceptions import CredentialsError
from typing import Dict
import pandas as pd

# Import Alpaca
from alpaca.trading.enums import (
    OrderSide as AlpacaOrderSide,
    OrderStatus as AlpacaOrderStatus,
    TimeInForce as AlpacaTIF)

from alpaca.common.exceptions import (
    APIError as AlpacaAPIError)

from alpaca.trading.requests import (
    MarketOrderRequest as AlpacaMarketOrderRequest)

from alpaca.data.requests import (
    StockLatestQuoteRequest as AlpacaStockLatestQuoteRequest)

# Import Mercury
from mercuryFramework.trader import Trader

from mercuryFramework.mercury_exceptions import (
    QtyAndNotionalError,
    InsufficientOrderArgumentsError,
    OrderSideError,
    TimeInForceError)

# Import Hermes
from hermesConnector.timeframe import TimeFrame
from hermesConnector.hermes_enums import (
    TimeframeUnit,
    OrderSide,
    TimeInForce)

from hermesConnector.models import (
    MarketOrderResult,
    LimitOrderResult)

from hermesConnector.connector_alpaca import Alpaca


# Configuration
# Load envirnoment
load_dotenv()


# Set pandas config
pd.set_option('display.max_colwidth', None)
# pd.set_option('display.large_repr', 'info')


# Client configuration
credentials = (os.getenv('ALPACA_PAPER_KEY'), os.getenv('ALPACA_PAPER_SECRET'))
if (
    (credentials[0] == None) or
    (credentials[0] == None)
    ):
    raise CredentialsError
mode = 'live'
tradingPair = 'AAPL'
tf = TimeFrame(1, TimeframeUnit.DAY)
dataPointsLimit = 100


# Define fixtures
@pytest.fixture
def mercuryInstance():
    trader = Trader(
        mode=mode,
        tradingPair=tradingPair,
        interval=tf,
        limit=dataPointsLimit,
        exchange='alpaca',
        credentials=credentials, # type: ignore
        updateCallback=None)
    
    trader.initialise()

    return trader


#
# Utilities
#

def cleanUpOrderGenerator(
        exchange: Alpaca,
        currentOrder,
        testOrderSide
):
    # Check if the order was partially filled, if so, submit an order against the filled amount
    # Process the quantity of filled portion of the test order
    filledQty = None
    if (currentOrder.filled_qty == None):
        raise ValueError
    else:
        filledQty = float(currentOrder.filled_qty)

    # Determine the opposite side of the trade
    cleanUpOrderSide = None
    if (testOrderSide == AlpacaOrderSide.BUY):
        cleanUpOrderSide = AlpacaOrderSide.SELL
    elif (testOrderSide == AlpacaOrderSide.SELL):
        cleanUpOrderSide = AlpacaOrderSide.BUY
    else:
        raise ValueError
    

    # Construct and submit the order
    cleanUpOrderReq = AlpacaMarketOrderRequest(
        symbol=tradingPair,
        qty=filledQty,
        side=cleanUpOrderSide,
        time_in_force=AlpacaTIF.DAY)
    cleanUpOrder = exchange._tradingClient.submit_order(cleanUpOrderReq)

def cleanUpSubmittedOrder(
        exchange: Alpaca,
        testOrderId,
        testOrderSide):
    currentOrder = exchange._tradingClient.get_order_by_id(order_id=testOrderId)
    if (isinstance(currentOrder, Dict)):
        raise TypeError

    if (
        (currentOrder.status != AlpacaOrderStatus.FILLED) and
        (currentOrder.status != AlpacaOrderStatus.PARTIALLY_FILLED)
    ):
        # The order was not filled, try to cancel it.
        try:
            exchange._tradingClient.cancel_order_by_id(testOrderId)
        except AlpacaAPIError as apiError:
            # Check if the order was filled between the status checking and the cancellation request. If so, prevent the race condition
            if (apiError.code == 42210000):
                # The order was already filled, unable to cancel it.
                # Qeury the order again
                currentOrder = exchange._tradingClient.get_order_by_id(order_id=testOrderId)
                if (isinstance(currentOrder, Dict)):
                    raise TypeError
                # Confirm that the order was filled
                if (
                    (currentOrder.status == AlpacaOrderStatus.FILLED) or
                    (currentOrder.status == AlpacaOrderStatus.PARTIALLY_FILLED)
                ):
                    cleanUpOrderGenerator(
                        exchange=exchange,
                        currentOrder=currentOrder,
                        testOrderSide=testOrderSide)
                pass
        return
    
    # The order hasn't been filled, generatre clean up order
    cleanUpOrderGenerator(
        exchange=exchange,
        currentOrder=currentOrder,
        testOrderSide=testOrderSide)
    
    

#
# Tests
#

def test_marketOrder(mercuryInstance: Trader):

    # Submit a correct order
    order = mercuryInstance.marketOrder(
        side=OrderSide.BUY,
        qty=1,
        tif=TimeInForce.DAY)
    assert isinstance(order, MarketOrderResult)

    # Clean up order
    cleanUpSubmittedOrder(
        mercuryInstance.exchange,
        order.order_id,
        AlpacaOrderSide.BUY)
    
    #
    # Invalid method calls
    #

    # Test 1: Both qty and notional supplied
    try:
        order = mercuryInstance.marketOrder(
            side=OrderSide.BUY,
            qty=1,
            notional=1000,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, QtyAndNotionalError) == True
    
    #
    # Test 2: No arguments supplied
    #
    try:
        order = mercuryInstance.marketOrder(
            side=OrderSide.BUY,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, InsufficientOrderArgumentsError) == True
    
    #
    # Test 3: Invalid arguments supplied
    #

    # Negative quantity
    try:
        order = mercuryInstance.marketOrder(
            side=OrderSide.BUY,
            qty=-1,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, InsufficientOrderArgumentsError) == True
    
    # Negative notional value
    try:
        order = mercuryInstance.marketOrder(
            side=OrderSide.BUY,
            notional=-1,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, InsufficientOrderArgumentsError) == True
    
    # Side not given
    try:
        order = mercuryInstance.marketOrder(
            side=None, # type: ignore   # For testing only, invalid intentionally.
            qty=1,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, OrderSideError) == True

    # Time in force not given
    try:
        order = mercuryInstance.marketOrder(
            side=OrderSide.BUY,
            qty=1,
            tif=None) # type: ignore   # For testing only, invalid intentionally. 
    except Exception as err:
        assert isinstance(err, TimeInForceError) == True




def test_limitOrder(mercuryInstance: Trader):

    # Get the current ask price for the limit orders
    # Request exchange directly
    quoteReq = AlpacaStockLatestQuoteRequest(
        symbol_or_symbols=tradingPair)
    latestQuote = mercuryInstance.exchange._historicalDataClient.get_stock_latest_quote(quoteReq) # type: ignore

    # Latest ask price
    latestAskPrice = float(latestQuote[tradingPair].ask_price)
    limitPrice = latestAskPrice - 10
    if (limitPrice <= 0):
        raise ValueError

    # Submit a correct order
    order = mercuryInstance.limitOrder(
        limitPrice=limitPrice,
        side=OrderSide.BUY,
        qty=1,
        tif=TimeInForce.DAY)
    assert isinstance(order, LimitOrderResult)

    # Clean up order
    cleanUpSubmittedOrder(
        mercuryInstance.exchange,
        order.order_id,
        AlpacaOrderSide.BUY)
    
    #
    # Invalid method calls
    #
    
    #
    # Test 1: No price arguments supplied
    #
    try:
        order = mercuryInstance.limitOrder(
            limitPrice=limitPrice,
            side=OrderSide.BUY,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, InsufficientOrderArgumentsError) == True
    
    #
    # Test 3: Invalid arguments supplied
    #

    # Negative quantity
    try:
        order = mercuryInstance.limitOrder(
            limitPrice=limitPrice,
            side=OrderSide.BUY,
            qty=-1,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, InsufficientOrderArgumentsError) == True
    
    try:
        order = mercuryInstance.limitOrder(
            limitPrice=-1,
            side=OrderSide.BUY,
            qty=1,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, InsufficientOrderArgumentsError) == True
    
    # Side not given
    try:
        order = mercuryInstance.limitOrder(
            limitPrice=limitPrice,
            side=None, # type: ignore   # For testing only, invalid intentionally.
            qty=1,
            tif=TimeInForce.DAY)
    except Exception as err:
        assert isinstance(err, OrderSideError) == True

    # Time in force not given
    try:
        order = mercuryInstance.limitOrder(
            limitPrice=limitPrice,
            side=OrderSide.BUY,
            qty=1,
            tif=None) # type: ignore   # For testing only, invalid intentionally. 
    except Exception as err:
        assert isinstance(err, TimeInForceError) == True

def test_historicData(mercuryInstance: Trader):
    # Checks for the indicator data calculated on the historic data.
    # The tests for the historic data itself is done on Hermes.

    # Get the columns for the indicators table
    columns = mercuryInstance.indicatorData.columns.drop("openTime")

    # Get the original list for indicators
    indicatorsKeys = list(mercuryInstance.indicatorFunctionParameters.keys())
    maKeys = list(mercuryInstance.movingAverageParams.keys())
    originalList = indicatorsKeys + maKeys

    # Check for the length
    assert len(columns) == len(originalList)

    # Check for each of the columns
    for col in originalList:
        assert (col in columns)

    # Check for the lnegth of the DataFrame and the length of the price DataFrame
    priceDfLen = len(mercuryInstance.data)
    indicatorDfLen = len(mercuryInstance.indicatorData)

    assert priceDfLen == indicatorDfLen

def test_placeholder(mercuryInstance: Trader):
    # orders = mercuryInstance.exchange._tradingClient.get_orders(
    #     AlpacaGetOrdersRequest(status=AlpacaQueryOrderStatus.ALL)
    # )
    # pprint(orders)
    pass