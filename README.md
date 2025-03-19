# Kucoin-grid-spot-trading-bot
Automated grid trading bot for KuCoin using CCXT, featuring Tor proxy support, trend detection, and dynamic grid adjustments for BTC/USDT trading.  
# KucoinGridBot

A Python-based grid trading bot for KuCoin, designed to trade BTC/USDT using the CCXT library. The bot supports Tor proxy for privacy, trend detection with SMA crossover, and dynamic grid adjustments based on price movements.

## Features
- Grid trading with configurable spacing and levels
- Trend detection using 10-period and 50-period SMA
- Automatic grid recentering based on price shifts or idle timeouts
- Tor proxy integration for enhanced privacy
- Detailed logging and profit tracking

## Requirements
- Python 3.7+
- CCXT library (`pip install ccxt`)
- python-dotenv (`pip install python-dotenv`)
- Tor service running locally (for proxy support)

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/TonyToniy/Kucoin-grid-spot-trading-bot.git
   cd KucoinGridBot

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3. Set up environment variables in a .env file:
```bash
KUCOIN_API_KEY=your_api_key
KUCOIN_SECRET=your_secret
KUCOIN_PASSWORD=your_password
```
4. Run the bot:
```bash
python grid_bot.py
```
Adjust the # Grid Trading Parameters to suit your trading account assets.
PS: The bot uses Tor proxy for countries where API trading is not supported by KuCoin.

Usage
Adjust grid parameters (e.g., grid_spacing, grid_levels) in the script.
Monitor logs in grid_bot.log for activity and profit updates.
Disclaimer
Trading involves risk. Use this bot at your own discretion and test thoroughly before deploying with real funds.

Example Adjustments:
Small Account (e.g., $100 USDT, 0.001 BTC):
python

```bash
grid_spacing = 100  # Smaller grid for tighter range
min_order_size = 0.0005  # Smaller order size
price_shift_threshold = 100  # Recenter on smaller moves
idle_timeout = 600  # 10 minutes to reduce frequent recentering
```
Large Account (e.g., $10,000 USDT, 0.1 BTC):
python
```bash
grid_spacing = 1000  # Wider grid for bigger swings
grid_levels = 3  # Multiple buy/sell levels
min_order_size = 0.005  # Larger order size
price_shift_threshold = 1000  # Recenter on bigger moves
```
Users should check their KuCoin balance (get_balance()) and adjust these based on available USDT and BTC, ensuring usdt_balance >= min_order_size * buy_price * 1.001 and btc_balance >= min_order_size.

Disclaimer
Trading involves risk. Use this bot at your own discretion and test thoroughly before deploying with real funds.






