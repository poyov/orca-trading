"""
Configuration centrale d'Orca Trading.
"""
import os
from pathlib import Path
from loguru import logger

class Settings:
    """Paramètres du projet."""
    
    # Chemins
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    NOTEBOOKS_DIR = BASE_DIR / "notebooks"
    
    # Trading
    SYMBOLS = ["BTC/USDT"]
    TIMEFRAMES = ["5m", "15m", "1h"]
    EXCHANGE = "binance"
    
    # Database
    DB_PATH = DATA_DIR / "processed" / "market.db"
    
    # Risk
    INITIAL_BALANCE = 10000.0
    COMMISSION = 0.001  # 0.1%
    MAX_POSITION_SIZE = 0.1  # 10%
    MAX_DRAWDOWN = 0.10  # 10%
    
    def __init__(self):
        """Initialise les répertoires."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.NOTEBOOKS_DIR.mkdir(exist_ok=True)
        self.DB_PATH.parent.mkdir(exist_ok=True)
        
        # Configuration des logs
        logger.remove()  # Enlève le handler par défaut
        logger.add(
            self.LOGS_DIR / "orca.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        # Ajoute aussi dans la console
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            level="INFO"
        )
    
    def show(self):
        """Affiche la configuration."""
        logger.info("=" * 50)
        logger.info("🐋 Configuration d'Orca Trading")
        logger.info("=" * 50)
        logger.info(f"Répertoire de base: {self.BASE_DIR}")
        logger.info(f"Symboles: {self.SYMBOLS}")
        logger.info(f"Timeframes: {self.TIMEFRAMES}")
        logger.info(f"Base de données: {self.DB_PATH}")
        logger.info("=" * 50)

# Instance globale
import sys
settings = Settings()
