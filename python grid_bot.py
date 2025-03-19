import ccxt
import logging
import time
import random
import requests
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    filename="grid_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# KuCoin API Keys
api_key = os.getenv('KUCOIN_API_KEY')
secret = os.getenv('KUCOIN_SECRET')
password = os.getenv('KUCOIN_PASSWORD')

# Grid Trading Parameters
pair = "BTC/USDT"
grid_spacing = 500
grid_levels = 1
min_order_size = 0.0011
trading_fee = 0.001
price_shift_threshold = grid_spacing  # Tightened to 1,000 USDT for faster recentering
idle_timeout = 300  # 5 minutes (seconds) before recentering if price is outside range

# Global state
total_profit = 0.0
grid_active = False
bot_start_time = time.time()
last_active_time = time.time()  # Track when grid was last "active" (orders filled)

# Configure Tor proxy session
session = requests.Session()
session.proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}
retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Initialize KuCoin exchange
exchange = ccxt.kucoin({
    'apiKey': api_key,
    'secret': secret,
    'password': password,
    'enableRateLimit': True,
    'session': session,
})

def fetch_candlestick_data(timeframe='1h', limit=50):
    """Fetch OHLCV data from KuCoin for trend analysis."""
    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
        return [(candle[0], float(candle[4])) for candle in ohlcv]
    except Exception as e:
        logging.error(f"Failed to fetch candlestick data: {e}")
        return []

def calculate_sma(prices, period):
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def detect_trend(candles):
    """Detect trend using SMA crossover (10-period vs 50-period)."""
    if not candles or len(candles) < 50:
        return "insufficient_data"
    close_prices = [candle[1] for candle in candles]
    sma_short = calculate_sma(close_prices, 10)
    sma_long = calculate_sma(close_prices, 50)
    if sma_short is None or sma_long is None:
        return "insufficient_data"
    if sma_short > sma_long:
        return "uptrend"
    elif sma_short < sma_long:
        return "downtrend"
    else:
        return "sideways"

def get_current_price():
    try:
        ticker = exchange.fetch_ticker(pair)
        return float(ticker['last'])
    except Exception as e:
        logging.error(f"Failed to fetch price: {e}")
        return None

def get_balance():
    try:
        balance = exchange.fetch_balance()
        usdt_free = float(balance['free'].get('USDT', 0))
        btc_free = float(balance['free'].get('BTC', 0))
        logging.info(f"Balance: USDT = {usdt_free:.8f}, BTC = {btc_free:.8f}")
        return usdt_free, btc_free
    except Exception as e:
        logging.error(f"Failed to fetch balance: {e}")
        return 0, 0

def fetch_open_orders():
    try:
        return exchange.fetch_open_orders(pair)
    except Exception as e:
        logging.error(f"Failed to fetch open orders: {e}")
        return []

def fetch_closed_orders():
    try:
        return exchange.fetch_closed_orders(pair, limit=100, since=int(bot_start_time * 1000))
    except Exception as e:
        logging.error(f"Failed to fetch closed orders: {e}")
        return []

def cancel_all_orders():
    open_orders = fetch_open_orders()
    if not open_orders:
        logging.info("No open orders to cancel.")
        return
    for order in open_orders:
        try:
            exchange.cancel_order(order['id'], pair)
            logging.info(f"Canceled order {order['id']}.")
            time.sleep(0.5)
        except Exception as e:
            logging.error(f"Failed to cancel order {order['id']}: {e}")

def calculate_sell_price(buy_price):
    return round(buy_price * (1 + 2 * trading_fee) + grid_spacing, 2)

def update_profit():
    global total_profit
    closed_orders = fetch_closed_orders()
    if not closed_orders:
        logging.info(f"Total profit so far: {total_profit:.2f} USDT")
        return
    total_profit = 0
    for order in closed_orders:
        if order['status'] == 'closed' and order['timestamp'] > bot_start_time * 1000:
            if order['side'] == 'sell':
                buy_price = order['price'] - grid_spacing - (order['price'] * 2 * trading_fee)
                profit = (order['price'] - buy_price) * order['amount'] - (order['cost'] * trading_fee * 2)
                total_profit += profit
    logging.info(f"Total profit so far: {total_profit:.2f} USDT")

def place_grid_orders(center_price=None):
    global grid_active
    if center_price is None:
        center_price = get_current_price()
    if not center_price:
        logging.error("Cannot place orders: No current price.")
        return center_price

    usdt_balance, btc_balance = get_balance()

    open_orders = fetch_open_orders()
    buy_orders = [o for o in open_orders if o['side'] == 'buy']
    sell_orders = [o for o in open_orders if o['side'] == 'sell']

    buy_price = round(center_price - grid_spacing, 2)
    sell_price = round(center_price + grid_spacing, 2)

    usdt_needed = min_order_size * buy_price * 1.001
    affordable_btc = min(btc_balance, min_order_size)
    affordable_usdt = min(usdt_balance / buy_price / 1.001, min_order_size)

    if not buy_orders and usdt_balance >= usdt_needed:
        try:
            order_size = max(min_order_size, affordable_usdt)
            exchange.create_limit_buy_order(pair, order_size, buy_price)
            logging.info(f"Placed BUY: {order_size:.8f} BTC at {buy_price} USDT")
            grid_active = True
        except Exception as e:
            logging.error(f"Failed BUY at {buy_price}: {e}")
    elif usdt_balance < usdt_needed:
        logging.info(f"Insufficient USDT for buy: Need {usdt_needed:.2f}, Have {usdt_balance:.2f}")
    else:
        logging.info("Buy order already exists. Skipping placement.")

    if not sell_orders and btc_balance >= min_order_size:
        try:
            order_size = max(min_order_size, affordable_btc)
            exchange.create_limit_sell_order(pair, order_size, sell_price)
            logging.info(f"Placed SELL: {order_size:.8f} BTC at {sell_price} USDT")
            grid_active = True
        except Exception as e:
            logging.error(f"Failed SELL at {sell_price}: {e}")
    elif btc_balance < min_order_size:
        logging.info(f"Insufficient BTC for sell: Need {min_order_size:.8f}, Have {btc_balance:.8f}")
    else:
        logging.info("Sell order already exists. Skipping placement.")

    if grid_active:
        logging.info(f"Grid initialized with center price {center_price}")
    return center_price

def monitor_and_replace_orders(center_price):
    global grid_active, last_active_time
    if not grid_active:
        return center_price

    current_price = get_current_price()
    if not current_price:
        return center_price

    buy_price = round(center_price - grid_spacing, 2)
    sell_price = round(center_price + grid_spacing, 2)

    # --- Trend Detection and Grid Adjustment ---
    candles = fetch_candlestick_data(timeframe='1h', limit=50)
    trend = detect_trend(candles)
    logging.info(f"Detected trend: {trend}")
    
    # Add trend shift threshold to prevent small adjustments
    trend_shift_threshold = 100  # Minimum price change to trigger grid shift (adjustable)
    if trend == "uptrend" and current_price > center_price + trend_shift_threshold:
        logging.info(f"Uptrend detected. Shifting grid up to {current_price}...")
        cancel_all_orders()
        grid_active = False
        return place_grid_orders(current_price)
    elif trend == "downtrend" and current_price < center_price - trend_shift_threshold:
        logging.info(f"Downtrend detected. Shifting grid down to {current_price}...")
        cancel_all_orders()
        grid_active = False
        return place_grid_orders(current_price)
    # Sideways or small movements: No adjustment

    # Check if price is outside grid range and idle for too long
    if (current_price < buy_price or current_price > sell_price):
        if time.time() - last_active_time > idle_timeout:
            logging.info(f"Price {current_price} outside grid range ({buy_price}-{sell_price}) for {idle_timeout}s. Recentering...")
            cancel_all_orders()
            grid_active = False
            return place_grid_orders(current_price)

    # Check if price exceeds shift threshold
    if abs(current_price - center_price) > price_shift_threshold:
        logging.info(f"Price moved significantly ({current_price} vs {center_price}). Recentering grid...")
        cancel_all_orders()
        grid_active = False
        return place_grid_orders(current_price)

    usdt_balance, btc_balance = get_balance()
    open_orders = fetch_open_orders()
    order_prices = {float(order['price']) for order in open_orders}

    if buy_price not in order_prices and usdt_balance >= min_order_size * buy_price * 1.001:
        try:
            order_size = max(min_order_size, usdt_balance / buy_price / 1.001)
            exchange.create_limit_buy_order(pair, order_size, buy_price)
            logging.info(f"Replaced BUY: {order_size:.8f} BTC at {buy_price} USDT")
            last_active_time = time.time()  # Update on order activity
        except Exception as e:
            logging.error(f"Failed to replace BUY at {buy_price}: {e}")

    if sell_price not in order_prices and btc_balance >= min_order_size:
        try:
            order_size = max(min_order_size, btc_balance)
            exchange.create_limit_sell_order(pair, order_size, sell_price)
            logging.info(f"Replaced SELL: {order_size:.8f} BTC at {sell_price} USDT")
            last_active_time = time.time()  # Update on order activity
        except Exception as e:
            logging.error(f"Failed to replace SELL at {sell_price}: {e}")

    logging.info(f"Monitoring: Center={center_price}, Current={current_price}, Grid active={grid_active}")
    return center_price

def grid_trading_loop():
    logging.info("Starting grid trading loop...")
    center_price = place_grid_orders()
    if not center_price:
        logging.error("Failed to initialize grid. Exiting.")
        return

    while True:
        try:
            center_price = monitor_and_replace_orders(center_price)
            update_profit()
            sleep_time = random.randint(30, 60)
            logging.info(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
        except Exception as e:
            logging.error(f"Loop error: {e}")
            time.sleep(10)

def shutdown():
    logging.info(f"Shutting down bot. Final profit: {total_profit:.2f} USDT")
    cancel_all_orders()
    logging.info("Bot shut down complete.")

if __name__ == "__main__":
    logging.info("Starting KuCoin Grid Trading Bot with Tor Proxy...")
    try:
        grid_trading_loop()
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
        shutdown()
