# MercuryFramework Custom Exceptions.
# By Anas Arkawi, 2025.


# Import modules
from typing import Literal


# Define models, Literals, and utilities
ErrorStringLiteral = Literal[
    "GENERIC_MERCURY_ERROR",
    "QTY_AND_NOTIONAL_FOUND",
    "ORDER_SIDE_NOT_SUPPLIED",
    "ORDER_ARGUMENTS_INSUFFICIENT"
]

class MercuryBaseException(Exception):
    errCode     : int
    errStr      : ErrorStringLiteral


#
# Exceptions
#

class GenericMercuryError(MercuryBaseException):
    errCode     = 1000
    errStr      = "GENERIC_MERCURY_ERROR"

class QtyAndNotionalError(MercuryBaseException):
    errCode     = 1001
    errStr      = "QTY_AND_NOTIONAL_FOUND"

class OrderSideError(MercuryBaseException):
    errCode     = 1002
    errStr      = "ORDER_SIDE_NOT_SUPPLIED"

class InsufficientOrderArgumentsError(MercuryBaseException):
    errCode     = 1003
    errStr      = "ORDER_ARGUMENTS_INSUFFICIENT"
