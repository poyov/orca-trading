"""
Core configuration for Orca Trading Bot.
"""
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """Data collection configuration."""
    symbols: List[str]
    timeframes: List[str]
    exchange: str
    db_path: Path
    max_days_history: int = 90  # Start small
    
    def __post_init__(self):
        if isinstance(self.db_path, str):
            self.db_path = Path(self.db_path)

@dataclass
class TradingConfig:
    """Trading parameters."""
    initial_balance: float = 10000.0
    commission: float = 0.001  # 0.1%
    max_position_size: float = 0.1  # 10%
    max_drawdown: float = 0.10  # 10%
    stop_loss: float = 0.02  # 2%

@dataclass
class ModelConfig:
    """Model training configuration."""
    training_episodes: int = 1000
    validation_split: float = 0.2
    batch_size: int = 32
    learning_rate: float = 0.001

class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).parent.parent.parent
        
        if config_path is None:
            config_path = self.project_root / "config" / "default.yaml"
        
        self.config_path = Path(config_path)
        self._load_config()
        
        # Initialize sub-configs
        self.data = DataConfig(
            symbols=self._get("data.symbols", ["BTC/USDT"]),
            timeframes=self._get("data.timeframes", ["5m", "15m", "1h"]),
            exchange=self._get("data.exchange", "binance"),
            db_path=self.project_root / "data" / "processed" / "market.db"
        )
        
        self.trading = TradingConfig(
            initial_balance=self._get("trading.initial_balance", 10000.0),
            commission=self._get("trading.commission", 0.001),
            max_position_size=self._get("trading.max_position_size", 0.1),
            max_drawdown=self._get("trading.max_drawdown", 0.10),
            stop_loss=self._get("trading.stop_loss", 0.02)
        )
        
        self.model = ModelConfig(
            training_episodes=self._get("model.training_episodes", 1000),
            validation_split=self._get("model.validation_split", 0.2),
            batch_size=self._get("model.batch_size", 32),
            learning_rate=self._get("model.learning_rate", 0.001)
        )
        
        # Ensure directories exist
        self._create_directories()
        
        logger.info("Configuration loaded successfully")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Loaded config from {self.config_path}")
        except FileNotFoundError:
            self._config = {}
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
    
    def _get(self, key: str, default: Any = None):
        """Get value from config using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            self.project_root / "data" / "raw",
            self.project_root / "data" / "processed",
            self.project_root / "logs",
            self.project_root / "notebooks",
            self.data.db_path.parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def show(self):
        """Display current configuration."""
        print("=" * 60)
        print("🐋 ORCA TRADING CONFIGURATION")
        print("=" * 60)
        print(f"\n📊 Data:")
        print(f"  Symbols: {self.data.symbols}")
        print(f"  Timeframes: {self.data.timeframes}")
        print(f"  Exchange: {self.data.exchange}")
        print(f"  Database: {self.data.db_path}")
        
        print(f"\n💰 Trading:")
        print(f"  Initial balance: ${self.trading.initial_balance:,.2f}")
        print(f"  Commission: {self.trading.commission*100:.1f}%")
        print(f"  Max position size: {self.trading.max_position_size*100:.0f}%")
        
        print(f"\n🤖 Model:")
        print(f"  Training episodes: {self.model.training_episodes}")
        print(f"  Validation split: {self.model.validation_split}")
        
        print(f"\n⚠️  Risk:")
        print(f"  Max drawdown: {self.trading.max_drawdown*100:.0f}%")
        print(f"  Stop loss: {self.trading.stop_loss*100:.0f}%")
        print("=" * 60)

# Global config instance
config = Config()