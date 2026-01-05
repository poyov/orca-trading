#!/usr/bin/env python3
"""
Script d'initialisation complet pour Orca.
À exécuter UNE fois au début.
"""
import os
import sys
import subprocess
from pathlib import Path

def print_step(step):
    print(f"\n{'='*60}")
    print(f"ÉTAPE: {step}")
    print(f"{'='*60}")

def run_cmd(cmd, exit_on_error=True):
    """Exécute une commande shell."""
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ Erreur: {result.stderr}")
        if exit_on_error:
            sys.exit(1)
        return False
    print(f"  ✅ Succès")
    return True

def main():
    print("🐋 ORCA - Initialisation du projet de trading")
    
    # Étape 1: Vérifier Git
    print_step("1. Vérification de Git")
    if not run_cmd("git --version", exit_on_error=False):
        print("  ⚠️  Git n'est pas installé. Installation...")
        run_cmd("sudo apt-get install git -y")  # Ubuntu/Debian
    
    # Étape 2: Créer la structure
    print_step("2. Création de la structure")
    
    # Dossiers
    directories = [
        "orca/config",
        "orca/data",
        "orca/models",
        "orca/utils",
        "notebooks",
        "scripts",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  📁 Créé: {directory}")
    
    # Fichiers Python vides
    py_files = [
        "orca/__init__.py",
        "orca/config/__init__.py",
        "orca/data/__init__.py",
        "orca/models/__init__.py",
        "orca/utils/__init__.py",
        "__init__.py"
    ]
    
    for file in py_files:
        Path(file).touch()
        print(f"  📄 Créé: {file}")
    
    # Étape 3: Créer les fichiers de configuration
    print_step("3. Fichiers de configuration")
    
    # .gitignore
    gitignore_content = """# Spyder
.spyproject/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv/

# Virtual Environment
venv/

# Database
*.db
*.sqlite
*.sqlite3

# Jupyter
.ipynb_checkpoints/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Data (ne pas versionner)
data/raw/
*.csv
*.parquet
*.feather
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("  📄 Créé: .gitignore")
    
    # requirements.txt
    requirements = """# Core
pandas>=2.0.0
numpy>=1.24.0
ccxt>=4.0.0
ta>=0.10.0

# ML Basics
scikit-learn>=1.3.0
gymnasium>=0.29.0

# Visualization
plotly>=5.17.0
matplotlib>=3.7.0

# Utilities
python-dotenv>=1.0.0
loguru>=0.7.0
tqdm>=4.65.0
pyyaml>=6.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("  📄 Créé: requirements.txt")
    
    # settings.py
    settings_content = '''"""
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
'''
    
    with open("orca/config/settings.py", "w", encoding="utf-8") as f:
        f.write(settings_content)
    print("  📄 Créé: orca/config/settings.py")
    
    # Étape 4: Setup de l'environnement
    print_step("4. Installation des dépendances")
    
    # Créer venv si pas existant
    if not Path("venv").exists():
        run_cmd(f"{sys.executable} -m venv venv")
    
    # Installer requirements
    if sys.platform == "win32":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    run_cmd(f"{pip_cmd} install --upgrade pip")
    run_cmd(f"{pip_cmd} install -r requirements.txt")
    
    # Étape 5: Initialiser Git
    print_step("5. Configuration Git")
    
    # Vérifier si déjà un repo Git
    if not Path(".git").exists():
        run_cmd("git init")
    
    # Configurer Git
    run_cmd('git config user.email "poyov@example.com"')
    run_cmd('git config user.name "poyov"')
    
    # Ajouter les fichiers
    run_cmd("git add .")
    run_cmd('git commit -m "Initial commit: Structure de base"')
    
    # Lier au repo distant
    run_cmd("git remote add origin https://github.com/poyov/orca-trading.git")
    run_cmd("git branch -M main")
    
    print("\n" + "="*60)
    print("🎉 INITIALISATION TERMINÉE!")
    print("="*60)
    print("\nProchaines étapes:")
    print("1. Dans Spyder: Tools → Preferences → Python interpreter")
    print("2. Sélectionner: /chemin/vers/orca-trading/venv/bin/python")
    print("3. Redémarrer Spyder")
    print("4. Exécuter: import orca; orca.config.settings.show()")
    print("\nPour Git dans Spyder:")
    print("- View → Panes → Git (cocher)")
    print("- Ou utiliser le terminal intégré")
    
    return True

if __name__ == "__main__":
    main()