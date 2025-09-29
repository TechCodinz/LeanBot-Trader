"""
Base strategy interface for LeanBot-Trader
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import pandas as pd

from ..core.models import OHLCV, Signal, OrderSide


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"Strategy.{name}")
        
        # Strategy state
        self.data = {}  # Historical data for each symbol
        self.indicators = {}  # Calculated indicators
        self.last_signals = {}  # Last signal for each symbol
    
    @abstractmethod
    def analyze(self, symbol: str, ohlcv_data: List[OHLCV]) -> Optional[Signal]:
        """Analyze market data and generate trading signals"""
        pass
    
    def update_data(self, symbol: str, ohlcv_data: List[OHLCV]) -> None:
        """Update historical data for a symbol"""
        # Convert OHLCV data to pandas DataFrame
        df_data = []
        for candle in ohlcv_data:
            df_data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        self.data[symbol] = df
        self.logger.debug(f"Updated data for {symbol}: {len(df)} candles")
    
    def calculate_sma(self, symbol: str, period: int, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average"""
        if symbol not in self.data:
            return pd.Series()
        
        return self.data[symbol][column].rolling(window=period).mean()
    
    def calculate_ema(self, symbol: str, period: int, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        if symbol not in self.data:
            return pd.Series()
        
        return self.data[symbol][column].ewm(span=period).mean()
    
    def calculate_rsi(self, symbol: str, period: int = 14, column: str = 'close') -> pd.Series:
        """Calculate Relative Strength Index"""
        if symbol not in self.data:
            return pd.Series()
        
        prices = self.data[symbol][column]
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        if symbol not in self.data or self.data[symbol].empty:
            return None
        
        return self.data[symbol]['close'].iloc[-1]


class SimpleSMAStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'short_window': 10,
            'long_window': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("SimpleSMA", default_params)
    
    def analyze(self, symbol: str, ohlcv_data: List[OHLCV]) -> Optional[Signal]:
        """Analyze market data using SMA crossover with RSI filter"""
        # Update data
        self.update_data(symbol, ohlcv_data)
        
        if symbol not in self.data or len(self.data[symbol]) < self.parameters['long_window']:
            self.logger.debug(f"Insufficient data for {symbol}")
            return None
        
        # Calculate indicators
        short_sma = self.calculate_sma(symbol, self.parameters['short_window'])
        long_sma = self.calculate_sma(symbol, self.parameters['long_window'])
        rsi = self.calculate_rsi(symbol, self.parameters['rsi_period'])
        
        if short_sma.empty or long_sma.empty or rsi.empty:
            return None
        
        # Get latest values
        latest_short = short_sma.iloc[-1]
        latest_long = long_sma.iloc[-1]
        prev_short = short_sma.iloc[-2] if len(short_sma) > 1 else latest_short
        prev_long = long_sma.iloc[-2] if len(long_sma) > 1 else latest_long
        latest_rsi = rsi.iloc[-1]
        latest_price = self.get_latest_price(symbol)
        
        if not all([latest_short, latest_long, latest_rsi, latest_price]):
            return None
        
        signal = None
        
        # Check for bullish crossover
        if (prev_short <= prev_long and latest_short > latest_long and 
            latest_rsi < self.parameters['rsi_overbought']):
            
            signal = Signal(
                symbol=symbol,
                action=OrderSide.BUY,
                price=latest_price,
                confidence=0.7,
                reason=f"SMA crossover bullish (RSI: {latest_rsi:.1f})",
                stop_loss=latest_price * 0.97,  # 3% stop loss
                take_profit=latest_price * 1.06   # 6% take profit
            )
        
        # Check for bearish crossover
        elif (prev_short >= prev_long and latest_short < latest_long and 
              latest_rsi > self.parameters['rsi_oversold']):
            
            signal = Signal(
                symbol=symbol,
                action=OrderSide.SELL,
                price=latest_price,
                confidence=0.7,
                reason=f"SMA crossover bearish (RSI: {latest_rsi:.1f})",
                stop_loss=latest_price * 1.03,  # 3% stop loss
                take_profit=latest_price * 0.94   # 6% take profit
            )
        
        # Store indicators for reference
        self.indicators[symbol] = {
            'short_sma': latest_short,
            'long_sma': latest_long,
            'rsi': latest_rsi,
            'price': latest_price
        }
        
        if signal:
            self.last_signals[symbol] = signal
            self.logger.info(f"Generated signal for {symbol}: {signal.action.value} @ {signal.price:.2f} - {signal.reason}")
        
        return signal