import sqlite3
from contextlib import contextmanager
from typing import Generator
from pathlib import Path
from src.config import DATABASE_PATH, SCHEMA_PATH


def get_db_path(custom_path: str | None = None) -> Path:
    """Return the resolved database path."""
    target = Path(custom_path) if custom_path else Path(DATABASE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


@contextmanager
def get_connection(custom_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection with row factory enabled."""
    db_path = get_db_path(custom_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate_db(custom_path: str | None = None) -> None:
    """Ensure newer columns and indexes exist in the SQLite database."""
    db_path = get_db_path(custom_path)
    with get_connection(str(db_path)) as conn:
        cursor = conn.cursor()
        # 1. Check offers table columns
        cursor.execute("PRAGMA table_info(offers)")
        existing_offer_cols = {row["name"] for row in cursor.fetchall()}
        if existing_offer_cols:
            if "variant_name" not in existing_offer_cols:
                cursor.execute("ALTER TABLE offers ADD COLUMN variant_name TEXT DEFAULT 'Standard'")
            if "condition" not in existing_offer_cols:
                cursor.execute("ALTER TABLE offers ADD COLUMN condition TEXT DEFAULT 'Brand New'")

        # 2. Check price_history table columns
        cursor.execute("PRAGMA table_info(price_history)")
        existing_hist_cols = {row["name"] for row in cursor.fetchall()}
        if existing_hist_cols:
            if "currency" not in existing_hist_cols:
                cursor.execute("ALTER TABLE price_history ADD COLUMN currency TEXT DEFAULT 'USD'")
            if "data_source" not in existing_hist_cols:
                cursor.execute("ALTER TABLE price_history ADD COLUMN data_source TEXT DEFAULT 'demo_seed'")
            if "data_status" not in existing_hist_cols:
                cursor.execute("ALTER TABLE price_history ADD COLUMN data_status TEXT DEFAULT 'demo'")

        # 3. Ensure indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if cursor.fetchone():
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_history'")
        if cursor.fetchone():
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_offer_date ON price_history(offer_id, recorded_at)")

        # 4. Phase 7: Ensure users table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'deactivated'))
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

        # 5. Phase 7: Ensure wishlist table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id)
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_product ON wishlist(product_id)")

        # 6. Phase 7: Ensure user_preferences table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                preferred_categories TEXT DEFAULT '[]',
                preferred_brands TEXT DEFAULT '[]',
                min_budget REAL,
                max_budget REAL,
                preferred_store_id INTEGER,
                sort_preference TEXT DEFAULT 'best_deal',
                priority TEXT DEFAULT 'balanced' CHECK(priority IN ('lowest_price', 'best_deal', 'balanced')),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (preferred_store_id) REFERENCES stores(id) ON DELETE SET NULL,
                CHECK(min_budget IS NULL OR min_budget >= 0),
                CHECK(max_budget IS NULL OR max_budget >= 0),
                CHECK(min_budget IS NULL OR max_budget IS NULL OR max_budget >= min_budget)
            )
            """
        )

        # 7. Phase 6 & 7: Ensure price_tracking table exists with user_id and multi-user uniqueness
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_tracking'")
        tracking_table_exists = cursor.fetchone() is not None

        if not tracking_table_exists:
            cursor.execute(
                """
                CREATE TABLE price_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER NOT NULL,
                    target_price REAL NOT NULL CHECK(target_price > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused')),
                    last_observed_price REAL,
                    last_checked_at TIMESTAMP,
                    last_alert_at TIMESTAMP,
                    last_alert_price REAL,
                    last_alert_type TEXT,
                    alert_trigger_type TEXT DEFAULT 'target_or_drop' CHECK(alert_trigger_type IN ('target_or_drop', 'target_only', 'drop_only')),
                    note TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    UNIQUE(user_id, product_id)
                )
                """
            )
        else:
            cursor.execute("PRAGMA table_info(price_tracking)")
            tracking_cols = {row["name"] for row in cursor.fetchall()}
            if "user_id" not in tracking_cols:
                # Migrate price_tracking safely to support user_id and composite unique constraint
                conn.execute("PRAGMA foreign_keys = OFF;")
                cursor.execute(
                    """
                    CREATE TABLE price_tracking_migrated (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        product_id INTEGER NOT NULL,
                        target_price REAL NOT NULL CHECK(target_price > 0),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused')),
                        last_observed_price REAL,
                        last_checked_at TIMESTAMP,
                        last_alert_at TIMESTAMP,
                        last_alert_price REAL,
                        last_alert_type TEXT,
                        alert_trigger_type TEXT DEFAULT 'target_or_drop' CHECK(alert_trigger_type IN ('target_or_drop', 'target_only', 'drop_only')),
                        note TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                        UNIQUE(user_id, product_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO price_tracking_migrated (
                        id, user_id, product_id, target_price, created_at, status,
                        last_observed_price, last_checked_at, last_alert_at,
                        last_alert_price, last_alert_type, alert_trigger_type, note
                    )
                    SELECT 
                        id, NULL, product_id, target_price, created_at, status,
                        last_observed_price, last_checked_at, last_alert_at,
                        last_alert_price, last_alert_type, alert_trigger_type, note
                    FROM price_tracking
                    """
                )
                cursor.execute("DROP TABLE price_tracking")
                cursor.execute("ALTER TABLE price_tracking_migrated RENAME TO price_tracking")
                conn.execute("PRAGMA foreign_keys = ON;")

        # 8. Phase 6 & 7: Ensure price_alerts table exists and has user_id
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_alerts'")
        alerts_table_exists = cursor.fetchone() is not None

        if not alerts_table_exists:
            cursor.execute(
                """
                CREATE TABLE price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tracking_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL CHECK(alert_type IN ('target_reached', 'price_drop')),
                    observed_price REAL NOT NULL,
                    previous_price REAL,
                    target_price REAL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
                    trigger_key TEXT UNIQUE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (tracking_id) REFERENCES price_tracking(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
                """
            )
        else:
            cursor.execute("PRAGMA table_info(price_alerts)")
            alerts_cols = {row["name"] for row in cursor.fetchall()}
            if "user_id" not in alerts_cols:
                cursor.execute("ALTER TABLE price_alerts ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
                cursor.execute(
                    """
                    UPDATE price_alerts
                    SET user_id = (SELECT user_id FROM price_tracking WHERE price_tracking.id = price_alerts.tracking_id)
                    """
                )

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracking_user ON price_tracking(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracking_product ON price_tracking(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracking_status ON price_tracking(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_tracking ON price_alerts(tracking_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_product ON price_alerts(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON price_alerts(is_read)")


def init_db(custom_path: str | None = None) -> None:
    """Initialize database tables using schema.sql and apply migrations."""
    db_path = get_db_path(custom_path)
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(str(db_path)) as conn:
        conn.executescript(schema_sql)

    migrate_db(custom_path)


