import subprocess
import sys
import importlib
import logging

# === Configuration des packages requis ===
REQUIRED_PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "ta": "ta",
    "requests": "requests",
    "python-dotenv": "dotenv",
    "matplotlib": "matplotlib",
    "selenium": "selenium",
    "webdriver-manager": "webdriver_manager",
    "tradingview_ta": "tradingview_ta"
}

# === Logger simple ===
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger()

def is_installed(import_name):
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def install_package(pip_name):
    log.info(f"🔧 Installation de '{pip_name}'...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        log.info(f"✅ '{pip_name}' installé avec succès.\n")
    except subprocess.CalledProcessError as e:
        log.error(f"❌ Échec installation de '{pip_name}' ({e})\n")

def check_dependencies():
    log.info("🔍 Vérification des packages requis...\n")
    for pip_name, import_name in REQUIRED_PACKAGES.items():
        if is_installed(import_name):
            log.info(f"✅ {pip_name} (OK)")
        else:
            log.warning(f"📦 {pip_name} manquant.")
            install_package(pip_name)
    log.info("\n🎯 Vérification terminée.\n")

if __name__ == "__main__":
    check_dependencies()
