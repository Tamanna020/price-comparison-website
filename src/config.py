import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = os.environ.get("PRICEWISE_DB_PATH", str(DATA_DIR / "pricewise.db"))
DATABASE_URL = os.environ.get("DATABASE_URL")
SCHEMA_PATH = DATA_DIR / "schema.sql"

# Environment & Security Configuration (Phase 12)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ("production", "prod")
SECRET_KEY = os.environ.get("SECRET_KEY", "pricewise-dev-secret-key-phase12-change-in-prod")
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))
MAX_UPLOAD_SIZE_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))  # 5 MB

# CORS Allowed Origins
RAW_CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")
CORS_ORIGINS = [o.strip() for o in RAW_CORS_ORIGINS.split(",") if o.strip()]

# Gemini Configuration
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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
