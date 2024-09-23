# Mercury / Quantitative Finance Made Accessible.

Mercury is a core package used in Lycon project which is a platform for traders to use and employ Quantitative Finance in their trading. The tool is still a work in progress and so far only works with Binance APIs.


# Example Usage

DISCLAIMER: this is just an example of how to interact with the llibrary, and it is not an example of a viable algorithm that can be used to trade for profit. Look at the **Disclaimer** section for more information on using this library to trade.

In the `main.py` file there's a short example algorithm which buys ETH when the RSI level is 40 or below, indicating that the asset may be oversold, and sells the bought ETH when the RSI level is 60 or above.


## Features

The package has many features including:

* **Price Acquisition**: The library has the code required to obtain historic data and update it as live data comes in.
* **Indicator Calculation**: The package contains all the needed functions and routines to calculate indicators for a given security.
* **Basic Algorithmic Trading**: By using simple functions you can define parameters for the bot to trade automatically based on market conditions.


## For the future

The future plans for the bot includes but not limited to:

* Adding various other indicators,
* Adding support for other exchanges,
* Improving runtime routines to be more robust,
* Implement more advanced algorithms,
* Implement more statistical analysis tools.


## Updates and more information

I will post regulat updates on the development of the project on my website in its designated section [here](http://anasarkawi.com/mercury/) and on my LinkedIn as reposts from the company page [here](https://www.linkedin.com/company/lycon).


## Licensing

The software is licensed under the *Mozilla Public License Version 2.0*. Details of the licensing can be found under the `LICENCE` file.

The software is provided in "as is" basis, with no warranty or liability. More information on the license file.


## Disclaimer

This is an on-going project with only one developer managing it. As of now, the code in this repository is not meant for production. Malfunctions and bugs are expected. Use this code at you own risk, the author of this code is not responsible for any damages or losses.