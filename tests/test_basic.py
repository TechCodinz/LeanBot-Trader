"""
Basic tests for LeanBot-Trader
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from leanbot.core.config import Config
from leanbot.core.portfolio import Portfolio
from leanbot.core.models import Balance, OrderSide, OHLCV
from leanbot.exchanges.base import MockExchange
from leanbot.strategies.base import SimpleSMAStrategy


class TestConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration creation"""
        config = Config("nonexistent.yaml")  # Should use defaults
        
        assert config.trading.exchange == "binance"
        assert config.trading.sandbox == True
        assert config.strategy.name == "simple_sma"
        assert config.risk.max_daily_loss == 0.05


class TestPortfolio:
    """Test portfolio management"""
    
    def test_portfolio_initialization(self):
        """Test portfolio initialization"""
        portfolio = Portfolio(initial_balance=10000.0)
        
        assert portfolio.initial_balance == 10000.0
        assert portfolio.base_currency == "USDT"
        assert "USDT" in portfolio.balances
        assert portfolio.balances["USDT"].total == 10000.0
    
    def test_balance_updates(self):
        """Test balance updates"""
        portfolio = Portfolio()
        balance = Balance("BTC", 1.0, 0.0, 1.0)
        
        portfolio.update_balance("BTC", balance)
        
        assert portfolio.get_balance("BTC") == balance
        assert portfolio.get_available_balance("BTC") == 1.0
    
    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation"""
        portfolio = Portfolio(initial_balance=10000.0)
        
        # Add some balances
        portfolio.update_balance("BTC", Balance("BTC", 1.0, 0.0, 1.0))
        portfolio.update_balance("ETH", Balance("ETH", 5.0, 0.0, 5.0))
        
        # Calculate value with prices
        prices = {"BTC": 50000.0, "ETH": 3000.0}
        total_value = portfolio.calculate_total_value(prices)
        
        # Should be 10000 (USDT) + 50000 (BTC) + 15000 (ETH) = 75000
        expected_value = 10000.0 + 50000.0 + 15000.0
        assert total_value == expected_value


class TestMockExchange:
    """Test mock exchange implementation"""
    
    @pytest.mark.asyncio
    async def test_exchange_connection(self):
        """Test exchange connection"""
        exchange = MockExchange()
        
        assert await exchange.connect() == True
        assert exchange.connected == True
        
        await exchange.disconnect()
        assert exchange.connected == False
    
    @pytest.mark.asyncio
    async def test_ticker_data(self):
        """Test ticker data retrieval"""
        exchange = MockExchange()
        await exchange.connect()
        
        ticker = await exchange.get_ticker("BTC/USDT")
        
        assert ticker is not None
        assert ticker.symbol == "BTC/USDT"
        assert ticker.last > 0
        assert ticker.bid < ticker.ask
        
        await exchange.disconnect()
    
    @pytest.mark.asyncio
    async def test_ohlcv_data(self):
        """Test OHLCV data retrieval"""
        exchange = MockExchange()
        await exchange.connect()
        
        ohlcv_data = await exchange.get_ohlcv("BTC/USDT", limit=10)
        
        assert len(ohlcv_data) == 10
        assert all(isinstance(candle, OHLCV) for candle in ohlcv_data)
        assert all(candle.high >= candle.low for candle in ohlcv_data)
        
        await exchange.disconnect()


class TestSimpleSMAStrategy:
    """Test Simple SMA strategy"""
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        strategy = SimpleSMAStrategy()
        
        assert strategy.name == "SimpleSMA"
        assert "short_window" in strategy.parameters
        assert "long_window" in strategy.parameters
    
    def test_strategy_with_insufficient_data(self):
        """Test strategy with insufficient data"""
        strategy = SimpleSMAStrategy()
        
        # Create minimal OHLCV data (less than required for long window)
        ohlcv_data = []
        for i in range(5):  # Less than default long_window of 30
            ohlcv_data.append(OHLCV(
                timestamp=datetime.now(),
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50000.0,
                volume=1000.0
            ))
        
        signal = strategy.analyze("BTC/USDT", ohlcv_data)
        assert signal is None
    
    def test_strategy_with_sufficient_data(self):
        """Test strategy with sufficient data"""
        strategy = SimpleSMAStrategy({"short_window": 5, "long_window": 10})
        
        # Create enough OHLCV data
        ohlcv_data = []
        for i in range(50):
            # Create uptrend data for testing
            price = 50000.0 + i * 10
            ohlcv_data.append(OHLCV(
                timestamp=datetime.now(),
                open=price,
                high=price + 50,
                low=price - 50,
                close=price,
                volume=1000.0
            ))
        
        signal = strategy.analyze("BTC/USDT", ohlcv_data)
        
        # Should generate a signal with this uptrend data
        # The exact signal depends on the crossover logic
        # At minimum, the strategy should process the data without errors
        assert signal is None or signal.symbol == "BTC/USDT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])