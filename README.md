# LeanBot-Trader 🚀

**No Limit to Trading**

A comprehensive cryptocurrency trading bot built with Python that supports multiple exchanges, strategies, and risk management features. LeanBot-Trader is designed to be modular, extensible, and production-ready.

## Features ✨

- **Multi-Exchange Support**: Extensible architecture for multiple cryptocurrency exchanges
- **Advanced Strategies**: Built-in trading strategies with technical indicators
- **Risk Management**: Comprehensive risk controls and position sizing
- **Portfolio Tracking**: Real-time portfolio monitoring and performance analytics
- **Backtesting**: Test strategies against historical data
- **Configuration-Driven**: YAML-based configuration for easy customization
- **Logging & Monitoring**: Detailed logging and performance metrics
- **CLI Interface**: Easy-to-use command-line interface
- **Mock Trading**: Safe testing environment with simulated trading
- **Async Architecture**: High-performance asynchronous design

## Quick Start 🚀

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/TechCodinz/LeanBot-Trader.git
cd LeanBot-Trader

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Configuration

```bash
# Initialize default configuration files
python main.py init
```

This creates:
- `config.yaml` - Main configuration file
- `.env` - Environment variables for API credentials

### 3. Configure Your Settings

Edit `config.yaml` to customize:
- Trading pairs and exchange settings
- Strategy parameters
- Risk management rules
- Logging preferences

Edit `.env` to add your exchange API credentials:
```bash
EXCHANGE_API_KEY=your_api_key_here
EXCHANGE_SECRET=your_secret_here
```

### 4. Validate Configuration

```bash
# Check if your configuration is valid
python main.py validate
```

### 5. Run the Bot

```bash
# Run in simulation mode (recommended for testing)
python main.py run --dry-run

# Run with live trading (use with caution)
python main.py run
```

## Configuration 📝

### Basic Configuration Structure

```yaml
# Trading Configuration
trading:
  exchange: "binance"
  sandbox: true
  symbols:
    - "BTC/USDT"
    - "ETH/USDT"
  max_position_size: 1000.0
  risk_per_trade: 0.02

# Strategy Configuration
strategy:
  name: "simple_sma"
  parameters:
    short_window: 10
    long_window: 30
    rsi_period: 14

# Risk Management
risk_management:
  max_daily_loss: 0.05
  max_drawdown: 0.15
  stop_loss_pct: 0.03
  take_profit_pct: 0.06
```

### Environment Variables

```bash
# Exchange API Credentials
EXCHANGE_API_KEY=your_api_key_here
EXCHANGE_SECRET=your_secret_here
EXCHANGE_PASSPHRASE=your_passphrase_here  # For some exchanges

# Sandbox/Testnet credentials (optional)
SANDBOX_API_KEY=your_sandbox_api_key
SANDBOX_SECRET=your_sandbox_secret
```

## Available Commands 🛠️

```bash
# Initialize configuration
python main.py init

# Validate configuration
python main.py validate

# Run the trading bot
python main.py run [--dry-run] [--config config.yaml]

# Show bot status and settings
python main.py status

# Test strategy on a specific symbol
python main.py test --symbol BTC/USDT
```

## Trading Strategies 📈

### Simple SMA Strategy

The included Simple Moving Average strategy uses:
- **Short-term SMA**: Fast moving average (default: 10 periods)
- **Long-term SMA**: Slow moving average (default: 30 periods)
- **RSI Filter**: Relative Strength Index for confirmation
- **Risk Controls**: Automatic stop-loss and take-profit levels

**Buy Signal**: Short SMA crosses above Long SMA + RSI < 70
**Sell Signal**: Short SMA crosses below Long SMA + RSI > 30

### Creating Custom Strategies

```python
from leanbot.strategies.base import BaseStrategy
from leanbot.core.models import Signal, OrderSide

class MyCustomStrategy(BaseStrategy):
    def analyze(self, symbol: str, ohlcv_data: List[OHLCV]) -> Optional[Signal]:
        # Implement your strategy logic here
        # Return Signal object or None
        pass
```

## Risk Management ⚠️

LeanBot-Trader includes comprehensive risk management:

- **Position Sizing**: Based on portfolio percentage and volatility
- **Stop-Loss Orders**: Automatic loss limitation
- **Take-Profit Orders**: Profit realization targets
- **Daily Loss Limits**: Maximum daily loss thresholds
- **Drawdown Protection**: Portfolio drawdown monitoring
- **Position Limits**: Maximum position size controls

## Architecture 🏗️

```
leanbot/
├── core/           # Core components
│   ├── bot.py      # Main bot logic
│   ├── config.py   # Configuration management
│   ├── models.py   # Data models
│   └── portfolio.py # Portfolio management
├── exchanges/      # Exchange interfaces
│   └── base.py     # Base exchange classes
├── strategies/     # Trading strategies
│   └── base.py     # Strategy implementations
├── risk/          # Risk management
├── data/          # Data management
└── utils/         # Utilities
```

## Development 🛠️

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run with coverage
python -m pytest tests/ --cov=leanbot
```

### Code Quality

```bash
# Format code
black leanbot/ tests/

# Check style
flake8 leanbot/ tests/

# Sort imports
isort leanbot/ tests/
```

## Safety & Disclaimers ⚠️

**IMPORTANT**: Cryptocurrency trading involves substantial risk of loss.

- **Always test thoroughly** in sandbox/simulation mode first
- **Start with small amounts** when going live
- **Never invest more than you can afford to lose**
- **Monitor your bot regularly** and have stop-loss mechanisms
- **Understand the risks** of automated trading

This software is provided "as is" without warranty. Use at your own risk.

## Contributing 🤝

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Roadmap 🗺️

- [ ] Additional exchange integrations (Binance, Coinbase, Kraken)
- [ ] More trading strategies (MACD, Bollinger Bands, ML-based)
- [ ] Advanced backtesting engine
- [ ] Web-based dashboard
- [ ] Paper trading mode
- [ ] Performance analytics and reporting
- [ ] Webhook notifications
- [ ] Docker deployment
- [ ] Cloud deployment guides

## Support 💬

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the wiki for detailed guides
- **Community**: Join discussions in GitHub Discussions

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Disclaimer**: This software is for educational and research purposes. Cryptocurrency trading carries significant financial risk. Always do your own research and never invest more than you can afford to lose.
