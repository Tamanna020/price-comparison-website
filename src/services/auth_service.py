"""Authentication and User Account Service for PriceWise AI (Phase 7).

Provides:
- Secure password hashing using PBKDF2-HMAC-SHA256 (NIST/OWASP standard, salted)
- Constant-time password verification to prevent timing attacks
- User registration with normalized email and input validation
- User login with status check and generic credential error messaging
- Profile update and password change operations
- Session state management helpers for Streamlit
"""

from datetime import datetime, timezone
import hashlib
import re
import secrets
from typing import Optional

from src.database.connection import get_connection, migrate_db
from src.database.models import User

# PBKDF2 parameters (OWASP recommended baseline)
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 260_000
SALT_BYTES = 16

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using salted PBKDF2-HMAC-SHA256.
    Returns: 'pbkdf2:sha256:260000$<salt_hex>$<hash_hex>'
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2:{PBKDF2_ALGORITHM}:{PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against a stored PBKDF2 hash using constant-time comparison.
    """
    if not plain_password or not stored_hash:
        return False

    try:
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False

        header, salt_hex, expected_hex = parts
        _, algo, iters_str = header.split(":")
        iterations = int(iters_str)
        salt = bytes.fromhex(salt_hex)

        derived = hashlib.pbkdf2_hmac(
            algo,
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return secrets.compare_digest(derived.hex(), expected_hex)
    except Exception:
        return False


def normalize_email(email: str) -> str:
    """Normalize email address by trimming whitespace and lowercasing."""
    return email.strip().lower() if email else ""


def validate_email_format(email: str) -> bool:
    """Validate standard email structure."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def register_user(
    email: str,
    password: str,
    display_name: str,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[User]]:
    """
    Register a new user account with hashed password and normalized email.
    
    Returns:
        (success: bool, message: str, user: Optional[User])
    """
    clean_name = (display_name or "").strip()
    clean_email = normalize_email(email)

    # 1. Validation
    if not clean_name:
        return False, "Display name is required.", None
    if len(clean_name) < 2:
        return False, "Display name must be at least 2 characters.", None

    if not clean_email or not validate_email_format(clean_email):
        return False, "Please enter a valid email address.", None

    if not password:
        return False, "Password is required.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    migrate_db(custom_path)

    pwd_hash = hash_password(password)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # 2. Check for duplicate email
        cursor.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
        if cursor.fetchone():
            return False, "An account with this email address already exists.", None

        # 3. Insert user
        cursor.execute(
            """
            INSERT INTO users (display_name, email, password_hash, created_at, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (clean_name, clean_email, pwd_hash, now_str),
        )
        user_id = cursor.lastrowid

        # 4. Initialize default user preferences row
        cursor.execute(
            """
            INSERT INTO user_preferences (user_id, preferred_categories, preferred_brands, updated_at)
            VALUES (?, '[]', '[]', ?)
            """,
            (user_id, now_str),
        )

        user = User(
            id=user_id,
            display_name=clean_name,
            email=clean_email,
            password_hash=pwd_hash,
            created_at=now_str,
            status="active",
        )

    return True, "Account registered successfully.", user


def authenticate_user(
    email: str,
    password: str,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[User]]:
    """
    Authenticate a user by email and password.
    Returns:
        (success: bool, message: str, user: Optional[User])
    """
    clean_email = normalize_email(email)
    if not clean_email or not password:
        return False, "Please provide both email and password.", None

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, display_name, email, password_hash, created_at, status
            FROM users
            WHERE email = ?
            """,
            (clean_email,),
        )
        row = cursor.fetchone()

        if not row:
            # Generic error to prevent account enumeration
            return False, "Invalid email address or password.", None

        stored_hash = str(row["password_hash"])
        if not verify_password(password, stored_hash):
            return False, "Invalid email address or password.", None

        if row["status"] != "active":
            return False, "Account is currently suspended or inactive.", None

        user = User(
            id=row["id"],
            display_name=str(row["display_name"]),
            email=str(row["email"]),
            password_hash=stored_hash,
            created_at=str(row["created_at"]),
            status=str(row["status"]),
        )

    return True, "Authentication successful.", user


def get_user_by_id(
    user_id: int,
    custom_path: Optional[str] = None,
) -> Optional[User]:
    """Retrieve user by primary key ID."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, display_name, email, password_hash, created_at, status FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return User(
            id=row["id"],
            display_name=str(row["display_name"]),
            email=str(row["email"]),
            password_hash=str(row["password_hash"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
        )


def get_user_by_email(
    email: str,
    custom_path: Optional[str] = None,
) -> Optional[User]:
    """Retrieve user by normalized email address."""
    clean_email = normalize_email(email)
    if not clean_email:
        return None

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, display_name, email, password_hash, created_at, status FROM users WHERE email = ?",
            (clean_email,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return User(
            id=row["id"],
            display_name=str(row["display_name"]),
            email=str(row["email"]),
            password_hash=str(row["password_hash"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
        )


def update_user_profile(
    user_id: int,
    display_name: str,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Update user's display name."""
    clean_name = (display_name or "").strip()
    if not clean_name:
        return False, "Display name cannot be empty."
    if len(clean_name) < 2:
        return False, "Display name must be at least 2 characters."

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET display_name = ? WHERE id = ?",
            (clean_name, user_id),
        )
        if cursor.rowcount == 0:
            return False, "User account not found."

    return True, "Profile updated successfully."


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Change a user's password with current password verification."""
    if not current_password or not new_password:
        return False, "Both current and new passwords are required."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    user = get_user_by_id(user_id, custom_path=custom_path)
    if not user:
        return False, "User account not found."

    if not verify_password(current_password, user.password_hash):
        return False, "Current password is incorrect."

    new_hash = hash_password(new_password)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id),
        )

    return True, "Password changed successfully."

