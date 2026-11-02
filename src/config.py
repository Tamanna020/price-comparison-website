import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = os.environ.get("PRICEWISE_DB_PATH", str(DATA_DIR / "pricewise.db"))
SCHEMA_PATH = DATA_DIR / "schema.sql"

# Application Metadata
APP_NAME = "PriceWise AI Beauty"
APP_TAGLINE = "Your beauty. Your budget. Your best match."
APP_VERSION = "1.0.0"
IS_DEMO_DATA = True
DEMO_BADGE_LABEL = "DEMO DATASET - ACADEMIC BEAUTY PROTOTYPE"
DEFAULT_CURRENCY = "₹"
DEMO_USER_EMAIL = "demo@pricewise.ai"
DEMO_USER_PASSWORD = "DemoPass123!"

# Clean SVG placeholder data URI for offline / fallback rendering
PRODUCT_IMAGE_FALLBACK = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='200' "
    "viewBox='0 0 300 200'><rect width='300' height='200' fill='%23FAF7F2'/><text x='50%25' "
    "y='45%25' dominant-baseline='middle' text-anchor='middle' font-size='42'>✨</text><text "
    "x='50%25' y='72%25' dominant-baseline='middle' text-anchor='middle' font-size='12' "
    "fill='%234A1D2F' font-family='sans-serif' font-weight='bold'>BEAUTY PRODUCT</text></svg>"
)

