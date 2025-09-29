"""
Exchange interface for LeanBot-Trader
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.models import Ticker, OHLCV, Order, Trade, Balance, Position


class ExchangeInterface(ABC):
    """Abstract base class for exchange interfaces"""
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the exchange"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get ticker data for a symbol"""
        pass
    
    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[OHLCV]:
        """Get OHLCV candlestick data"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Balance]:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> Dict[str, Position]:
        """Get open positions"""
        pass
    
    @abstractmethod
    async def create_order(self, order: Order) -> Optional[Order]:
        """Create a new order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get order status"""
        pass
    
    @abstractmethod
    async def get_trades(self, symbol: str = None, limit: int = 100) -> List[Trade]:
        """Get recent trades"""
        pass


class MockExchange(ExchangeInterface):
    """Mock exchange for testing and backtesting"""
    
    def __init__(self, api_key: str = "mock", api_secret: str = "mock", sandbox: bool = True):
        super().__init__(api_key, api_secret, sandbox)
        self.connected = False
        self.balance = {"USDT": Balance("USDT", 10000.0, 0.0, 10000.0)}
        self.positions = {}
        self.orders = {}
        self.trades = []
        self.order_counter = 0
        
        # Mock price data
        self.prices = {
            "BTC/USDT": 50000.0,
            "ETH/USDT": 3000.0,
            "ADA/USDT": 1.5
        }
    
    async def connect(self) -> bool:
        """Connect to mock exchange"""
        self.connected = True
        self.logger.info("Connected to mock exchange")
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from mock exchange"""
        self.connected = False
        self.logger.info("Disconnected from mock exchange")
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get mock ticker data"""
        if symbol not in self.prices:
            return None
        
        price = self.prices[symbol]
        return Ticker(
            symbol=symbol,
            bid=price * 0.999,
            ask=price * 1.001,
            last=price,
            volume=1000000.0
        )
    
    async def get_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[OHLCV]:
        """Get mock OHLCV data"""
        if symbol not in self.prices:
            return []
        
        price = self.prices[symbol]
        ohlcv_data = []
        
        for i in range(limit):
            # Generate mock data with small variations
            open_price = price * (1 + (i % 5 - 2) * 0.001)
            high = open_price * 1.005
            low = open_price * 0.995
            close = open_price * (1 + (i % 3 - 1) * 0.002)
            volume = 1000.0 + (i % 10) * 100
            
            ohlcv_data.append(OHLCV(
                timestamp=datetime.now(),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume
            ))
        
        return ohlcv_data
    
    async def get_balance(self) -> Dict[str, Balance]:
        """Get mock account balance"""
        return self.balance.copy()
    
    async def get_positions(self) -> Dict[str, Position]:
        """Get mock positions"""
        return self.positions.copy()
    
    async def create_order(self, order: Order) -> Optional[Order]:
        """Create mock order"""
        self.order_counter += 1
        order.id = f"mock_order_{self.order_counter}"
        
        # Simulate immediate fill for market orders
        if order.type.value == "market":
            ticker = await self.get_ticker(order.symbol)
            if ticker:
                fill_price = ticker.ask if order.side.value == "buy" else ticker.bid
                order.price = fill_price
                order.filled = order.amount
                order.remaining = 0.0
                order.cost = order.amount * fill_price
                order.status = order.status.CLOSED
                
                # Update mock balance
                base, quote = order.symbol.split('/')
                if order.side.value == "buy":
                    # Buy: reduce quote, increase base
                    if quote in self.balance:
                        self.balance[quote].free -= order.cost
                        self.balance[quote].total -= order.cost
                    
                    if base not in self.balance:
                        self.balance[base] = Balance(base, 0.0, 0.0, 0.0)
                    self.balance[base].free += order.amount
                    self.balance[base].total += order.amount
                else:
                    # Sell: reduce base, increase quote
                    if base in self.balance:
                        self.balance[base].free -= order.amount
                        self.balance[base].total -= order.amount
                    
                    if quote not in self.balance:
                        self.balance[quote] = Balance(quote, 0.0, 0.0, 0.0)
                    self.balance[quote].free += order.cost
                    self.balance[quote].total += order.cost
        
        self.orders[order.id] = order
        self.logger.info(f"Created mock order: {order.id}")
        return order
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel mock order"""
        if order_id in self.orders:
            self.orders[order_id].status = self.orders[order_id].status.CANCELED
            self.logger.info(f"Canceled mock order: {order_id}")
            return True
        return False
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get mock order"""
        return self.orders.get(order_id)
    
    async def get_trades(self, symbol: str = None, limit: int = 100) -> List[Trade]:
        """Get mock trades"""
        return self.trades[-limit:] if self.trades else []