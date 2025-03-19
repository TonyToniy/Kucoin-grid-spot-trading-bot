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
   git clone https://github.com/yourusername/KucoinGridBot.git
   cd KucoinGridBot

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3. Set up environment variables in a .env file:
```bash
KUCOIN_API_KEY=your_api_key
KUCOIN_SECRET=your_secret
KUCOIN_PASSWORD=your_password

4. Run the bot:
```bash
python grid_bot.py

Adjust the # Grid Trading Parameters to suit your trading account assets.
The bot uses tor prroxy for countries that API trading is not supported by Kucoin. 

