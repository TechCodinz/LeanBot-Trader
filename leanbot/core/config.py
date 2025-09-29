"""
Configuration management for LeanBot-Trader
"""
import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    exchange: str = "binance"
    sandbox: bool = True
    symbols: list = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    max_position_size: float = 1000.0
    risk_per_trade: float = 0.02


@dataclass
class StrategyConfig:
    """Strategy configuration parameters"""
    name: str = "simple_sma"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.15
    stop_loss_pct: float = 0.03
    take_profit_pct: float = 0.06


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file: str = "logs/leanbot.log"
    max_size: str = "10MB"
    backup_count: int = 5


class Config:
    """Main configuration class for LeanBot-Trader"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Load environment variables
        load_dotenv()
        
        # Default config file
        if config_file is None:
            config_file = "config.yaml"
        
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_file} not found. Using defaults.")
            config_data = {}
        
        # Load configuration sections
        self.trading = TradingConfig(**config_data.get('trading', {}))
        self.strategy = StrategyConfig(**config_data.get('strategy', {}))
        self.risk = RiskConfig(**config_data.get('risk_management', {}))
        self.logging = LoggingConfig(**config_data.get('logging', {}))
        
        # Load API credentials from environment
        self.api_key = os.getenv('EXCHANGE_API_KEY', '')
        self.api_secret = os.getenv('EXCHANGE_SECRET', '')
        self.api_passphrase = os.getenv('EXCHANGE_PASSPHRASE', '')
        
        # Sandbox credentials
        if self.trading.sandbox:
            self.api_key = os.getenv('SANDBOX_API_KEY', self.api_key)
            self.api_secret = os.getenv('SANDBOX_SECRET', self.api_secret)
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        if not self.api_key:
            errors.append("API key not found in environment variables")
        
        if not self.api_secret:
            errors.append("API secret not found in environment variables")
        
        if self.trading.risk_per_trade <= 0 or self.trading.risk_per_trade > 1:
            errors.append("Risk per trade must be between 0 and 1")
        
        if self.risk.max_daily_loss <= 0 or self.risk.max_daily_loss > 1:
            errors.append("Max daily loss must be between 0 and 1")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'trading': self.trading.__dict__,
            'strategy': self.strategy.__dict__,
            'risk_management': self.risk.__dict__,
            'logging': self.logging.__dict__
        }