"""
Portfolio management for LeanBot-Trader
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .models import Balance, Position, Trade, OrderSide


@dataclass
class PortfolioStats:
    """Portfolio statistics"""
    total_value: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_percent: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0


class Portfolio:
    """Portfolio management class"""
    
    def __init__(self, initial_balance: float = 10000.0, base_currency: str = "USDT"):
        self.logger = logging.getLogger(__name__)
        self.base_currency = base_currency
        self.initial_balance = initial_balance
        
        # Portfolio state
        self.balances: Dict[str, Balance] = {}
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        
        # Performance tracking
        self.stats = PortfolioStats()
        self.equity_curve: List[Dict] = []
        self.daily_returns: List[float] = []
        
        # Initialize base currency balance
        self.balances[base_currency] = Balance(
            currency=base_currency,
            free=initial_balance,
            used=0.0,
            total=initial_balance
        )
        
        self.logger.info(f"Portfolio initialized with {initial_balance} {base_currency}")
    
    def update_balance(self, currency: str, balance: Balance) -> None:
        """Update balance for a currency"""
        self.balances[currency] = balance
        self.logger.debug(f"Updated balance for {currency}: {balance}")
    
    def update_balances(self, balances: Dict[str, Balance]) -> None:
        """Update all balances"""
        self.balances.update(balances)
        self.logger.debug(f"Updated {len(balances)} balances")
    
    def get_balance(self, currency: str) -> Optional[Balance]:
        """Get balance for a currency"""
        return self.balances.get(currency)
    
    def get_available_balance(self, currency: str) -> float:
        """Get available balance for a currency"""
        balance = self.get_balance(currency)
        return balance.free if balance else 0.0
    
    def update_position(self, symbol: str, position: Position) -> None:
        """Update position for a symbol"""
        if position.size == 0:
            # Close position if size is zero
            if symbol in self.positions:
                del self.positions[symbol]
                self.logger.info(f"Closed position for {symbol}")
        else:
            self.positions[symbol] = position
            self.logger.debug(f"Updated position for {symbol}: {position}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self.positions.get(symbol)
    
    def get_total_position_value(self) -> float:
        """Get total value of all positions"""
        total_value = 0.0
        for position in self.positions.values():
            total_value += position.market_value
        return total_value
    
    def add_trade(self, trade: Trade) -> None:
        """Add a completed trade to the portfolio"""
        self.trades.append(trade)
        self.logger.info(f"Added trade: {trade.symbol} {trade.side.value} {trade.amount} @ {trade.price}")
        
        # Update statistics
        self._update_stats()
    
    def calculate_total_value(self, current_prices: Dict[str, float] = None) -> float:
        """Calculate total portfolio value"""
        total_value = 0.0
        
        # Add cash balances
        for balance in self.balances.values():
            if balance.currency == self.base_currency:
                total_value += balance.total
            elif current_prices and balance.currency in current_prices:
                # Convert to base currency
                total_value += balance.total * current_prices[balance.currency]
        
        # Add position values
        for position in self.positions.values():
            total_value += position.market_value
        
        return total_value
    
    def calculate_pnl(self) -> float:
        """Calculate total profit and loss"""
        total_pnl = 0.0
        
        # Realized PnL from trades
        for trade in self.trades:
            if trade.side == OrderSide.SELL:
                # For simplicity, assuming we track PnL at trade level
                total_pnl += trade.cost - trade.fee
        
        # Unrealized PnL from open positions
        for position in self.positions.values():
            total_pnl += position.unrealized_pnl
        
        return total_pnl
    
    def _update_stats(self) -> None:
        """Update portfolio statistics"""
        if not self.trades:
            return
        
        # Calculate win rate
        winning_trades = sum(1 for trade in self.trades if trade.side == OrderSide.SELL and trade.cost > 0)
        total_trades = len([t for t in self.trades if t.side == OrderSide.SELL])
        
        self.stats.total_trades = total_trades
        self.stats.winning_trades = winning_trades
        self.stats.losing_trades = total_trades - winning_trades
        self.stats.win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate total PnL
        self.stats.total_pnl = self.calculate_pnl()
        self.stats.total_pnl_percent = (self.stats.total_pnl / self.initial_balance) * 100
    
    def record_equity_point(self, current_prices: Dict[str, float] = None) -> None:
        """Record current equity for performance tracking"""
        equity = self.calculate_total_value(current_prices)
        equity_point = {
            'timestamp': datetime.now(),
            'equity': equity,
            'pnl': equity - self.initial_balance,
            'pnl_percent': ((equity - self.initial_balance) / self.initial_balance) * 100
        }
        self.equity_curve.append(equity_point)
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        return {
            'total_value': self.calculate_total_value(),
            'total_pnl': self.stats.total_pnl,
            'total_pnl_percent': self.stats.total_pnl_percent,
            'positions': len(self.positions),
            'total_trades': self.stats.total_trades,
            'win_rate': self.stats.win_rate,
            'balances': {currency: balance.total for currency, balance in self.balances.items()}
        }