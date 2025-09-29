"""
Core data models for LeanBot-Trader
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"


@dataclass
class Ticker:
    """Market ticker data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OHLCV:
    """OHLCV candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Order:
    """Trading order"""
    id: Optional[str] = None
    symbol: str = ""
    type: OrderType = OrderType.MARKET
    side: OrderSide = OrderSide.BUY
    amount: float = 0.0
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.OPEN
    filled: float = 0.0
    remaining: float = 0.0
    cost: float = 0.0
    fee: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trade:
    """Executed trade"""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    amount: float
    price: float
    cost: float
    fee: float
    timestamp: datetime = field(default_factory=datetime.now)
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Trading position"""
    symbol: str
    side: OrderSide
    size: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.size * self.current_price
    
    @property
    def pnl_percent(self) -> float:
        """PnL as percentage"""
        if self.entry_price == 0:
            return 0.0
        
        if self.side == OrderSide.BUY:
            return (self.current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - self.current_price) / self.entry_price


@dataclass
class Balance:
    """Account balance"""
    currency: str
    free: float
    used: float
    total: float
    
    @property
    def available(self) -> float:
        """Available balance"""
        return self.free


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    action: OrderSide
    price: float
    confidence: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None