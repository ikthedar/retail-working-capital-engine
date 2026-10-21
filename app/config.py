import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
REAL_CSV_PATH = KNOWLEDGE_DIR / "5. Inventory Till Oct 19th - Inventory Stock Tracking.csv"
SAMPLE_CSV_PATH = BASE_DIR / "data" / "sample" / "sample_ledger.csv"

# Dual-Profile Data Resolution:
# 1. Custom path via environment variable (e.g. for production hosting)
# 2. Local real family business CSV (if present on local machine)
# 3. Clean generic demo sample (for public GitHub cloners)
env_csv = os.getenv("INVENTORY_CSV_PATH")
if env_csv and Path(env_csv).exists():
    DEFAULT_CSV_PATH = Path(env_csv)
elif REAL_CSV_PATH.exists():
    DEFAULT_CSV_PATH = REAL_CSV_PATH
else:
    DEFAULT_CSV_PATH = SAMPLE_CSV_PATH

DB_PATH = BASE_DIR / "inventory.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# Financial & Engine Defaults
DEFAULT_BASE_YEAR = 2025
DEFAULT_AS_OF_DATE = "2026-10-19"  # Matches snapshot max date
CURRENCY_SYMBOL = "৳"

# Horizon Definitions (in days)
HORIZONS = {
    "1w": {"label": "1 Week", "days": 7},
    "2w": {"label": "2 Weeks", "days": 14},
    "1m": {"label": "1 Month", "days": 30},
    "3m": {"label": "3 Months", "days": 90},
    "6m": {"label": "6 Months", "days": 180},
    "12m": {"label": "12 Months", "days": 365},
    "all": {"label": "All Time", "days": None},
}

# Velocity Classification Defaults (Days of Inventory)
VELOCITY_THRESHOLDS = {
    "fast": 45,       # <= 45 days
    "medium": 90,     # 46 - 90 days
    "slow": 180,      # 91 - 180 days
    # > 180 days or 0 sales = dead stock
}
