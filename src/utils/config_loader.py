"""
Configuration loader for Orca Trading Bot.
"""
import yaml
import os
from pathlib import Path
from loguru import logger

class Config:
    """Singleton configuration class."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from YAML file."""
        config_paths = [
            "config/default.yaml",
            "../config/default.yaml",
            "./config/default.yaml"
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.data = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {path}")
                return
        
        # Fallback to default config
        self.data = {
            "project": {"name": "orca-trading", "version": "0.1.0"},
            "data": {
                "exchange": "binance",
                "symbols": ["BTC/USDT"],
                "timeframes": ["5m", "1h"]
            }
        }
        logger.warning("No config file found, using defaults")
    
    def get(self, key: str, default=None):
        """Get configuration value by dot notation."""
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def __getitem__(self, key):
        return self.get(key)

def load_config():
    """Helper function to load configuration."""
    return Config()

# Test the config loader
if __name__ == "__main__":
    config = load_config()
    print(f"Project: {config.get('project.name')}")
    print(f"Symbols: {config.get('data.symbols')}")