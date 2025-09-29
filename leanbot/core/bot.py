"""
Main LeanBot-Trader bot implementation
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .config import Config
from .portfolio import Portfolio
from .models import Order, OrderType, OrderSide, OrderStatus, Signal
from ..exchanges import ExchangeInterface, MockExchange
from ..strategies import BaseStrategy, SimpleSMAStrategy


class LeanBot:
    """Main trading bot class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize components
        self.portfolio = Portfolio(base_currency="USDT")
        self.exchange: Optional[ExchangeInterface] = None
        self.strategy: Optional[BaseStrategy] = None
        
        # Bot state
        self.running = False
        self.last_update = {}  # Last update time for each symbol
        self.active_orders = {}  # Track active orders
        
        # Performance tracking
        self.start_time = None
        self.stats = {
            'signals_generated': 0,
            'orders_placed': 0,
            'successful_trades': 0,
            'failed_orders': 0
        }
        
        self.logger.info("LeanBot initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("LeanBot")
        logger.setLevel(getattr(logging, self.config.logging.level))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        try:
            import os
            os.makedirs(os.path.dirname(self.config.logging.file), exist_ok=True)
            file_handler = logging.FileHandler(self.config.logging.file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize bot components"""
        try:
            # Initialize exchange
            self.exchange = self._create_exchange()
            if not await self.exchange.connect():
                self.logger.error("Failed to connect to exchange")
                return False
            
            # Initialize strategy
            self.strategy = self._create_strategy()
            
            # Load initial portfolio state
            await self._load_portfolio_state()
            
            self.logger.info("Bot initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def _create_exchange(self) -> ExchangeInterface:
        """Create exchange interface"""
        # For now, always use MockExchange for safety
        # In production, you would create the appropriate exchange based on config
        return MockExchange(
            api_key=self.config.api_key,
            api_secret=self.config.api_secret,
            sandbox=self.config.trading.sandbox
        )
    
    def _create_strategy(self) -> BaseStrategy:
        """Create trading strategy"""
        strategy_name = self.config.strategy.name
        
        if strategy_name == "simple_sma":
            return SimpleSMAStrategy(self.config.strategy.parameters)
        else:
            self.logger.warning(f"Unknown strategy: {strategy_name}, using default")
            return SimpleSMAStrategy()
    
    async def _load_portfolio_state(self) -> None:
        """Load portfolio state from exchange"""
        try:
            # Update balances
            balances = await self.exchange.get_balance()
            self.portfolio.update_balances(balances)
            
            # Update positions
            positions = await self.exchange.get_positions()
            for symbol, position in positions.items():
                self.portfolio.update_position(symbol, position)
            
            self.logger.info("Portfolio state loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load portfolio state: {e}")
    
    async def run(self) -> None:
        """Main bot execution loop"""
        if not await self.initialize():
            self.logger.error("Bot initialization failed")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Starting bot execution loop")
        
        try:
            while self.running:
                await self._trading_cycle()
                await asyncio.sleep(60)  # Wait 1 minute between cycles
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            await self.shutdown()
    
    async def _trading_cycle(self) -> None:
        """Execute one trading cycle"""
        try:
            # Update portfolio state
            await self._load_portfolio_state()
            
            # Process each symbol
            for symbol in self.config.trading.symbols:
                await self._process_symbol(symbol)
            
            # Record portfolio performance
            self.portfolio.record_equity_point()
            
            # Log summary
            self._log_cycle_summary()
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
    
    async def _process_symbol(self, symbol: str) -> None:
        """Process trading logic for a symbol"""
        try:
            # Get market data
            ohlcv_data = await self.exchange.get_ohlcv(symbol, timeframe="1m", limit=100)
            if not ohlcv_data:
                self.logger.warning(f"No market data for {symbol}")
                return
            
            # Generate signal
            signal = self.strategy.analyze(symbol, ohlcv_data)
            if signal:
                self.stats['signals_generated'] += 1
                await self._execute_signal(signal)
            
            # Check existing orders
            await self._check_orders(symbol)
            
            self.last_update[symbol] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {e}")
    
    async def _execute_signal(self, signal: Signal) -> None:
        """Execute a trading signal"""
        try:
            # Check if we already have a position or pending order
            existing_position = self.portfolio.get_position(signal.symbol)
            if existing_position and existing_position.side == signal.action:
                self.logger.debug(f"Already have position in {signal.symbol}")
                return
            
            # Calculate position size based on risk management
            position_size = self._calculate_position_size(signal)
            if position_size <= 0:
                self.logger.warning(f"Position size too small for {signal.symbol}")
                return
            
            # Create order
            order = Order(
                symbol=signal.symbol,
                type=OrderType.MARKET,
                side=signal.action,
                amount=position_size,
                price=signal.price
            )
            
            # Place order
            executed_order = await self.exchange.create_order(order)
            if executed_order:
                self.active_orders[executed_order.id] = executed_order
                self.stats['orders_placed'] += 1
                self.logger.info(f"Placed order: {executed_order.id} for {signal.symbol}")
            else:
                self.stats['failed_orders'] += 1
                self.logger.error(f"Failed to place order for {signal.symbol}")
                
        except Exception as e:
            self.logger.error(f"Error executing signal for {signal.symbol}: {e}")
    
    def _calculate_position_size(self, signal: Signal) -> float:
        """Calculate position size based on risk management"""
        # Get available balance
        available_balance = self.portfolio.get_available_balance("USDT")
        
        # Calculate position size based on risk per trade
        risk_amount = available_balance * self.config.trading.risk_per_trade
        
        # Calculate position size (simplified)
        position_value = min(risk_amount / 0.03, self.config.trading.max_position_size)  # 3% risk per position
        position_size = position_value / signal.price
        
        return position_size
    
    async def _check_orders(self, symbol: str) -> None:
        """Check status of active orders for a symbol"""
        orders_to_remove = []
        
        for order_id, order in self.active_orders.items():
            if order.symbol != symbol:
                continue
            
            try:
                updated_order = await self.exchange.get_order(order_id, symbol)
                if updated_order:
                    if updated_order.status in [OrderStatus.CLOSED, OrderStatus.CANCELED, OrderStatus.EXPIRED]:
                        orders_to_remove.append(order_id)
                        
                        if updated_order.status == OrderStatus.CLOSED:
                            self.stats['successful_trades'] += 1
                            self.logger.info(f"Order completed: {order_id}")
                        else:
                            self.logger.info(f"Order {order_id} status: {updated_order.status.value}")
            
            except Exception as e:
                self.logger.error(f"Error checking order {order_id}: {e}")
        
        # Remove completed orders
        for order_id in orders_to_remove:
            del self.active_orders[order_id]
    
    def _log_cycle_summary(self) -> None:
        """Log summary of current cycle"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        self.logger.info(
            f"Cycle Summary - "
            f"Portfolio Value: ${portfolio_summary['total_value']:.2f}, "
            f"PnL: ${portfolio_summary['total_pnl']:.2f} ({portfolio_summary['total_pnl_percent']:.2f}%), "
            f"Positions: {portfolio_summary['positions']}, "
            f"Active Orders: {len(self.active_orders)}"
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the bot"""
        self.logger.info("Shutting down bot...")
        
        try:
            # Cancel all active orders
            if self.active_orders:
                self.logger.info(f"Canceling {len(self.active_orders)} active orders")
                for order_id, order in self.active_orders.items():
                    try:
                        await self.exchange.cancel_order(order_id, order.symbol)
                    except Exception as e:
                        self.logger.error(f"Error canceling order {order_id}: {e}")
            
            # Disconnect from exchange
            if self.exchange:
                await self.exchange.disconnect()
            
            # Log final stats
            self._log_final_stats()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.logger.info("Bot shutdown completed")
    
    def _log_final_stats(self) -> None:
        """Log final bot statistics"""
        runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        self.logger.info(
            f"Final Stats - "
            f"Runtime: {runtime}, "
            f"Signals Generated: {self.stats['signals_generated']}, "
            f"Orders Placed: {self.stats['orders_placed']}, "
            f"Successful Trades: {self.stats['successful_trades']}, "
            f"Failed Orders: {self.stats['failed_orders']}, "
            f"Final Portfolio Value: ${portfolio_summary['total_value']:.2f}, "
            f"Total PnL: ${portfolio_summary['total_pnl']:.2f} ({portfolio_summary['total_pnl_percent']:.2f}%)"
        )