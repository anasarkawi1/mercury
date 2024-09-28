# Connector Library Main Abstraction Module
# By Anas Arkawi, 2023.


__all__ = ["connector_binance"]


# Own module import
from .connector_binance import Binance


# Main connector library
# The connector library will set up the standard routines according to the target exchange.
class Connector:
    # Exchange selector
    # According to the exchange value given, the correct connector sub-library will be inherited and will be made available. The client is authorised through the credentials given through the credentials library which is checked for validity before a connection is attempted.
    def exchangeSelect(self, exchange, credentials, options):
        exchangeInstance = None
        match exchange:
            case "binance":
                exchangeInstance = Binance(
                    mode=options["mode"],
                    tradingPair=options["tradingPair"],
                    interval=options["interval"],
                    limit=options["limit"],
                    credentials=credentials,
                    wshandler=options["dataHandler"],
                    columns=options["columns"])

            case _:
                return "EXCHANGE_INVALID"
            
        return exchangeInstance

    def __init__(self, exchange, credentials, options):
        self.exchange = self.exchangeSelect(exchange=exchange, credentials=credentials, options=options)