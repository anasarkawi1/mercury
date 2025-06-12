# Mercury Test Script
# By Anas Arkawi, 2025.


# Import modules
import pytest
from dotenv import load_dotenv
import os
from mercuryFramework.mercury_exceptions import CredentialsError


# Import Mercury
from mercuryFramework.trader import Trader

# Import Hermes
from hermesConnector.timeframe import TimeFrame
from hermesConnector.hermes_enums import TimeframeUnit


# Configuration
# Load envirnoment
load_dotenv()

# Client configuration
credentials = (os.getenv('ALPACA_PAPER_KEY'), os.getenv('ALPACA_PAPER_SECRET'))
if (type(credentials) != tuple[str, str]):
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
# Tests
#

def test_marketOrder(mercuryInstance):
    pass

def test_limitOrder(mercuryInstance):
    pass

def test_historicData(mercuryInstance):
    pass