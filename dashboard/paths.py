from pathlib import Path

# project root
BASE_DIR = Path(__file__).resolve().parent.parent

# data/dashboard directory
DASHBOARD_DIR = BASE_DIR / "data" / "dashboard"
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

# canonical paths
DB_PATH = DASHBOARD_DIR / "trades.db"
REPORT_PATH = DASHBOARD_DIR / "report.html"
