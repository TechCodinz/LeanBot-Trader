#!/usr/bin/env python3
"""
LeanBot-Trader: A comprehensive cryptocurrency trading bot
Command-line interface for running the trading bot
"""
import asyncio
import click
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from leanbot.core.config import Config
from leanbot.core.bot import LeanBot


@click.group()
@click.version_option(version="1.0.0", prog_name="LeanBot-Trader")
def cli():
    """LeanBot-Trader: No Limit to Trading
    
    A comprehensive cryptocurrency trading bot with multiple strategies,
    risk management, and portfolio tracking capabilities.
    """
    pass


@cli.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Run in simulation mode without real trades')
def run(config, dry_run):
    """Run the trading bot"""
    try:
        # Load configuration
        bot_config = Config(config)
        
        # Validate configuration
        if not bot_config.validate():
            click.echo("❌ Configuration validation failed", err=True)
            sys.exit(1)
        
        # Force sandbox mode for dry runs
        if dry_run:
            bot_config.trading.sandbox = True
            click.echo("🔧 Running in dry-run mode (sandbox enabled)")
        
        # Create and run bot
        bot = LeanBot(bot_config)
        
        click.echo("🚀 Starting LeanBot-Trader...")
        click.echo(f"📊 Exchange: {bot_config.trading.exchange}")
        click.echo(f"🎯 Strategy: {bot_config.strategy.name}")
        click.echo(f"💰 Symbols: {', '.join(bot_config.trading.symbols)}")
        click.echo(f"⚡ Sandbox Mode: {bot_config.trading.sandbox}")
        
        # Run the bot
        asyncio.run(bot.run())
        
    except KeyboardInterrupt:
        click.echo("\n⏹️  Bot stopped by user")
    except Exception as e:
        click.echo(f"❌ Error running bot: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
def validate(config):
    """Validate configuration file"""
    try:
        bot_config = Config(config)
        if bot_config.validate():
            click.echo("✅ Configuration is valid")
        else:
            click.echo("❌ Configuration validation failed", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error validating config: {e}", err=True)
        sys.exit(1)


@cli.command()
def init():
    """Initialize a new LeanBot-Trader configuration"""
    try:
        # Check if config already exists
        if os.path.exists('config.yaml'):
            if not click.confirm('config.yaml already exists. Overwrite?'):
                click.echo("Initialization cancelled")
                return
        
        # Copy example config
        import shutil
        shutil.copy('config.example.yaml', 'config.yaml')
        
        # Copy example .env
        if not os.path.exists('.env'):
            shutil.copy('.env.example', '.env')
        
        click.echo("✅ Initialized LeanBot-Trader configuration")
        click.echo("📝 Edit config.yaml to customize your settings")
        click.echo("🔑 Edit .env to add your API credentials")
        click.echo("🚀 Run 'python main.py run' to start trading")
        
    except Exception as e:
        click.echo(f"❌ Error initializing config: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
def status(config):
    """Show bot status and portfolio summary"""
    try:
        bot_config = Config(config)
        
        click.echo("📊 LeanBot-Trader Status")
        click.echo("=" * 40)
        click.echo(f"Exchange: {bot_config.trading.exchange}")
        click.echo(f"Strategy: {bot_config.strategy.name}")
        click.echo(f"Symbols: {', '.join(bot_config.trading.symbols)}")
        click.echo(f"Sandbox Mode: {bot_config.trading.sandbox}")
        click.echo(f"Max Position Size: ${bot_config.trading.max_position_size}")
        click.echo(f"Risk Per Trade: {bot_config.trading.risk_per_trade * 100}%")
        
        # Strategy parameters
        click.echo("\n🎯 Strategy Parameters:")
        for key, value in bot_config.strategy.parameters.items():
            click.echo(f"  {key}: {value}")
        
        # Risk management
        click.echo("\n⚠️  Risk Management:")
        click.echo(f"  Max Daily Loss: {bot_config.risk.max_daily_loss * 100}%")
        click.echo(f"  Max Drawdown: {bot_config.risk.max_drawdown * 100}%")
        click.echo(f"  Stop Loss: {bot_config.risk.stop_loss_pct * 100}%")
        click.echo(f"  Take Profit: {bot_config.risk.take_profit_pct * 100}%")
        
    except Exception as e:
        click.echo(f"❌ Error getting status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--symbol', '-s', required=True, help='Trading symbol (e.g., BTC/USDT)')
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
def test(symbol, config):
    """Test strategy on a specific symbol"""
    async def run_test():
        try:
            bot_config = Config(config)
            bot = LeanBot(bot_config)
            
            if not await bot.initialize():
                click.echo("❌ Failed to initialize bot", err=True)
                return
            
            click.echo(f"🧪 Testing strategy on {symbol}...")
            
            # Get market data
            ohlcv_data = await bot.exchange.get_ohlcv(symbol, timeframe="1m", limit=100)
            if not ohlcv_data:
                click.echo(f"❌ No market data for {symbol}", err=True)
                return
            
            # Test strategy
            signal = bot.strategy.analyze(symbol, ohlcv_data)
            
            if signal:
                click.echo(f"📈 Signal Generated:")
                click.echo(f"  Action: {signal.action.value.upper()}")
                click.echo(f"  Price: ${signal.price:.2f}")
                click.echo(f"  Confidence: {signal.confidence:.1%}")
                click.echo(f"  Reason: {signal.reason}")
                if signal.stop_loss:
                    click.echo(f"  Stop Loss: ${signal.stop_loss:.2f}")
                if signal.take_profit:
                    click.echo(f"  Take Profit: ${signal.take_profit:.2f}")
            else:
                click.echo("📊 No signal generated")
            
            # Show indicators
            if symbol in bot.strategy.indicators:
                indicators = bot.strategy.indicators[symbol]
                click.echo(f"\n📊 Current Indicators:")
                for key, value in indicators.items():
                    if isinstance(value, float):
                        click.echo(f"  {key}: {value:.2f}")
                    else:
                        click.echo(f"  {key}: {value}")
            
            await bot.shutdown()
            
        except Exception as e:
            click.echo(f"❌ Error testing strategy: {e}", err=True)
    
    asyncio.run(run_test())


if __name__ == '__main__':
    cli()