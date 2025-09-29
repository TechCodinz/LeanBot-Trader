"""
LeanBot-Trader: A comprehensive cryptocurrency trading bot
"""

__version__ = "1.0.0"
__author__ = "TechCodinz"
__description__ = "No Limit to Trading"

from .core.bot import LeanBot
from .core.config import Config
from .core.portfolio import Portfolio

__all__ = ["LeanBot", "Config", "Portfolio"]