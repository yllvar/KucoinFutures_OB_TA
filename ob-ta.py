import os
import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
from dotenv import load_dotenv
from tabulate import tabulate
import time
import logging

# Load environment variables from .env file if present
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
PASSPHRASE = os.getenv('PASSPHRASE')
SYMBOLS = ['ETH/USDT:USDT', 'ARB/USDT:USDT', 'SOL/USDT:USDT', 'AGLD/USDT:USDT', 'BTC/USDT:USDT', 'MATIC/USDT:USDT']
TIMEFRAMES = ['5m', '15m', '1h', '4h']
THRESHOLD_POSITIVE = 70
THRESHOLD_NEGATIVE = -90
LIMIT_ENTRY_PARAMETERS = {
    'ETH/USDT': {'limit': 100, 'threshold_positive': 50, 'threshold_negative': -75},
    'ARB/USDT': {'limit': 100, 'threshold_positive': 50, 'threshold_negative': -75},
    'SOL/USDT': {'limit': 100, 'threshold_positive': 50, 'threshold_negative': -75},
    'AGLD/USDT': {'limit': 100, 'threshold_positive': 50, 'threshold_negative': -75},
    'BTC/USDT': {'limit': 100, 'threshold_positive': 50, 'threshold_negative': -75},
    'MATIC/USDT': {'limit': 100, 'threshold_positive': 50, 'threshold_negative': -75}
}
ORDER_BOOK_DEPTH = 20
BID_VOLUME_RATIO_THRESHOLD = 0.4
ASK_VOLUME_RATIO_THRESHOLD = 0.6
AGGREGATION_INTERVAL = 60

def fetch_ohlcvs(exchange, symbol, timeframe):
    try:
        # Fetch OHLCV data
        ohlcvs = exchange.fetch_ohlcv(symbol, timeframe=timeframe)

        if not ohlcvs:
            raise ValueError(f"No OHLCV data available for symbol: {symbol}")

        # Create DataFrame
        df = pd.DataFrame(ohlcvs, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Check if the 'close' column is present in the DataFrame
        if 'close' not in df:
            raise KeyError("OHLCV data does not contain 'close' column")

        return df

    except ccxt.BaseError as e:
        logger.error(f"Error fetching OHLCV data for symbol {symbol} and timeframe {timeframe}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame to indicate no valid data available
    except Exception as e:
        logger.error(f"Error processing OHLCV data for symbol {symbol} and timeframe {timeframe}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame to indicate an error occurred

# Function to fetch Level 3 order book data
def fetch_l3_order_book(exchange, symbol, limit=None):
    try:
        # Fetch Level 3 order book data
        order_book = exchange.fetch_order_book(symbol, limit=limit, params={'level': 2})

        if 'bids' not in order_book or 'asks' not in order_book:
            raise KeyError("Invalid order book data")

        bids = order_book['bids']
        asks = order_book['asks']

        return bids, asks

    except ccxt.BaseError as e:
        logger.error(f"Error fetching Level 3 order book data for symbol {symbol}: {e}")
        return None, None


# Function to fetch order book data with limit entry parameters
def fetch_order_book_with_limit(exchange, symbol, limit):
    try:
        # Fetch order book data
        order_book = exchange.fetch_order_book(symbol, limit=limit)

        if 'bids' not in order_book or 'asks' not in order_book:
            raise KeyError("Invalid order book data")

        bids = order_book['bids']
        asks = order_book['asks']

        return bids, asks

    except ccxt.BaseError as e:
        logger.error(f"Error fetching order book data for symbol {symbol}: {e}")
        return None, None

# Function to calculate total bid and ask volumes and order book imbalance
def calculate_order_book_metrics(bids, asks):
    if bids is None or asks is None:
        return None, None, None

    bid_volume = sum([bid[1] for bid in bids])
    ask_volume = sum([ask[1] for ask in asks])
    order_book_imbalance = bid_volume - ask_volume

    return bid_volume, ask_volume, order_book_imbalance

# Function to determine entry signal based on order book imbalance and other conditions
def determine_entry_signal(order_book_imbalance, close_price, threshold_positive, threshold_negative, ask_volume_ratio, sma20):
    if order_book_imbalance is None or ask_volume_ratio is None or sma20 is None:
        return 'No Entry Signal'

    if (
        order_book_imbalance > threshold_positive
        and ask_volume_ratio > ASK_VOLUME_RATIO_THRESHOLD
        and close_price > sma20
    ):
        entry_signal = f"Enter Long Position at {close_price} (Place Limit Order at {close_price})"
    elif (
        order_book_imbalance < threshold_negative
        and ask_volume_ratio > ASK_VOLUME_RATIO_THRESHOLD
        and close_price < sma20
    ):
        entry_signal = f"Enter Short Position at {close_price} (Place Limit Order at {close_price})"
    else:
        entry_signal = 'No Entry Signal'

    return entry_signal

def print_order_book_analysis(symbol, bid_volume, ask_volume, order_book_imbalance, close_price):
    print("Order Book Analysis for symbol", symbol)
    print("Bid Volume:", bid_volume)
    print("Ask Volume:", ask_volume)
    print("Market Strength:", "Strong buying pressure and market strength" if bid_volume > ask_volume else "Strong selling pressure and market weakness")
    print("Order Book Imbalance:", "Buy pressure dominates the market (bullish sentiment)" if order_book_imbalance > 0 else "Sell pressure dominates the market (bearish sentiment)" if order_book_imbalance < 0 else "Balanced order book")
    print("Close Price:", close_price)
    print()

# Function to calculate support and resistance levels for a DataFrame
def calculate_support_resistance_levels(df):
    if 'low' not in df or 'high' not in df:
        raise KeyError("Invalid DataFrame columns")

    support_level = np.min(df['low'])
    resistance_level = np.max(df['high'])

    return support_level, resistance_level

# Function to calculate SMA20 for a DataFrame
def calculate_sma20(df):
    # Ensure the 'close' column is present
    if 'close' not in df:
        raise KeyError("Invalid DataFrame columns. 'close' column is required for SMA calculation.")

    # Calculate SMA20
    df['sma20'] = ta.sma(df['close'], length=20)  # Use the 'sma' method from the 'ta' library

    return df
    
# Function to print the consolidated analysis data
def print_consolidated_analysis(analysis_data, bids, asks):
    consolidated_analysis = []

    for symbol, data in analysis_data.items():
        entry_signal = data['Entry Signal']
        bid_volume = data['Bid Volume']
        ask_volume = data['Ask Volume']
        order_book_imbalance = data['Order Book Imbalance']
        close_price = data['Close Price']

        for timeframe in TIMEFRAMES:
            symbol_data = data['Symbol Data'][timeframe]

            support_level = symbol_data['support_level']
            resistance_level = symbol_data['resistance_level']
            sma20 = symbol_data['sma20']

            # Calculate bid-ask spread and volatility for each timeframe
            spread = bids[0][0] - asks[0][0]
            volatility = (resistance_level - support_level) / support_level * 100

            # Determine market strength and trend for each timeframe
            market_strength = "Strong buying pressure and market strength" if bid_volume > ask_volume else "Strong selling pressure and market weakness"
            trend = "Bullish market trend" if close_price > resistance_level else "Bearish market trend" if close_price < support_level else "Neutral market trend"

            # Append the data to the consolidated analysis list
            consolidated_analysis.append({
                'Symbol': symbol,
                'Timeframe': timeframe,
                'Entry Signal': entry_signal,
                'Bid Volume': bid_volume,
                'Ask Volume': ask_volume,
                'Order Book Imbalance': order_book_imbalance,
                'Close Price': close_price,
                'Market Strength': market_strength,
                'Trend': trend,
                'Support Level': support_level,
                'Resistance Level': resistance_level,
                'Bid-Ask Spread': spread,
                'Volatility (%)': volatility
            })

    logger.info(tabulate(consolidated_analysis, headers='keys', tablefmt='grid'))
    
# Function to perform analysis for a symbol with aggregated order book data
def perform_analysis_with_aggregation(exchange, symbol):
    symbol_data = {}

    for timeframe in TIMEFRAMES:
        # Fetch OHLCV data
        ohlcvs = fetch_ohlcvs(exchange, symbol, timeframe)

        if ohlcvs is None:
            continue

        # Calculate SMA20
        ohlcvs = calculate_sma20(ohlcvs)

        # Calculate support and resistance levels for each timeframe
        support_level, resistance_level = calculate_support_resistance_levels(ohlcvs)

        # Store the OHLCV data and SMA20 for the timeframe in the dictionary
        symbol_data[timeframe] = {
            'ohlcvs': ohlcvs,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'sma20': ohlcvs['sma20']  # Store the SMA20 values in the dictionary
        }

    if not symbol_data:
        logger.warning(f"No valid OHLCV data available for symbol {symbol}")
        return None, None, None  # Return None for bids and asks as well

    # Fetch Level 3 order book data with aggregation
    bids, asks = fetch_l3_order_book(exchange, symbol)

    # Fetch order book data with limit entry parameters
    limit_entry_params = LIMIT_ENTRY_PARAMETERS.get(symbol, {})
    bids, asks = fetch_order_book_with_limit(exchange, symbol, limit=limit_entry_params.get('limit', 100))

    # Calculate total bid and ask volumes and order book imbalance
    bid_volume, ask_volume, order_book_imbalance = calculate_order_book_metrics(bids, asks)

    # Fetch the close price from the OHLCV data (using the smallest timeframe)
    close_price = symbol_data[TIMEFRAMES[0]]['ohlcvs']['close'].iloc[-1]

    # Calculate ask volume ratio
    ask_volume_ratio = ask_volume / bid_volume

    # Determine entry signal based on order book imbalance and other conditions
    entry_signal = determine_entry_signal(
        order_book_imbalance,
        close_price,
        THRESHOLD_POSITIVE,
        THRESHOLD_NEGATIVE,
        ask_volume_ratio,
        symbol_data[TIMEFRAMES[0]]['sma20'].iloc[-1]  # Access SMA20 from the dictionary
    )

    return {
        'Symbol': symbol,
        'Entry Signal': entry_signal,
        'Bid Volume': bid_volume,
        'Ask Volume': ask_volume,
        'Order Book Imbalance': order_book_imbalance,
        'Close Price': close_price,
        'Symbol Data': symbol_data
    }, bids, asks  # Return bids and asks variables

# Function to run the main analysis loop
def main():
    # Create an instance of the Kucoin Futures exchange
    exchange = ccxt.kucoinfutures({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'password': PASSPHRASE,
        'enableRateLimit': True  # Adjust as needed
    })

    # Initialize the analysis data dictionary
    analysis_data = {}

    # Run the main analysis loop
    try:
        while True:
            bids = None
            asks = None
            for symbol in SYMBOLS:
                try:
                    data, symbol_bids, symbol_asks = perform_analysis_with_aggregation(exchange, symbol)
                    if data is not None:
                        analysis_data[symbol] = data

                    # Store the bids and asks variables
                    bids = symbol_bids
                    asks = symbol_asks

                except Exception as e:
                    logger.error(f"Error performing analysis for symbol {symbol}: {e}")

            # Print the consolidated analysis data
            print_consolidated_analysis(analysis_data, bids, asks)

            # Sleep for dynamic sleep duration before the next iteration (e.g., 300 seconds)
            sleep_duration = 300
            logger.info(f"Sleeping for {sleep_duration} seconds...")
            time.sleep(sleep_duration)

    except KeyboardInterrupt:
        logger.info("Terminating the analysis.")

if __name__ == "__main__":
    main()


