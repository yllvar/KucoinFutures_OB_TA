# Crypto Trading Analysis with Aggregated Order Book Data

This project is a Python script that performs crypto trading analysis using aggregated order book data. It fetches historical OHLCV (Open, High, Low, Close, Volume) data for selected symbols from a cryptocurrency exchange and calculates various trading indicators, support/resistance levels, and entry signals based on order book metrics.

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Crypto Trading Analysis with Aggregated Order Book Data is a Python script that combines historical price data with real-time order book data to perform trading analysis for selected cryptocurrency symbols. The script calculates the Simple Moving Average (SMA) over different timeframes and identifies potential entry signals for long and short positions based on order book metrics.

The script uses the ccxt library to interact with the Kucoin Futures exchange and fetches both OHLCV data and Level 3 order book data for the specified symbols. The analysis is performed using popular Python libraries such as pandas, pandas_ta, and numpy.

## Prerequisites

Before running the script, ensure you have the following prerequisites installed:

1. Python 3.7 or higher
2. ccxt library (`pip install ccxt`)
3. pandas library (`pip install pandas`)
4. pandas_ta library (`pip install pandas_ta`)
5. numpy library (`pip install numpy`)
6. dotenv library (`pip install python-dotenv`)

## Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/cryptotrading-analysis.git
cd cryptotrading-analysis

Install the required Python libraries using pip:
pip install ccxt pandas pandas_ta numpy python-dotenv

## Configuration
Before running the script, you need to provide your Kucoin Futures API credentials in the .env file. Create a new file named .env in the project root directory and add the following lines:

API_KEY=YOUR_KUCOIN_API_KEY
SECRET_KEY=YOUR_KUCOIN_SECRET_KEY
PASSPHRASE=YOUR_KUCOIN_PASSPHRASE

Replace YOUR_KUCOIN_API_KEY, YOUR_KUCOIN_SECRET_KEY, and YOUR_KUCOIN_PASSPHRASE with your actual Kucoin Futures API credentials. (Passphrase is not your trading passwords)

## Usage
To run the analysis script, simply execute the main Python script:

python main.py

The script will fetch historical OHLCV data, calculate SMA, fetch order book data, and analyze the trading signals for the specified symbols and timeframes. The analysis results will be displayed on the console, and the script will keep running to provide real-time updates at regular intervals.

Contributing
If you would like to contribute to this project, you can fork the repository and create a pull request with your proposed changes. 

Freelance
I'm open for a freelance job in the nieche of algorithmic trading 

