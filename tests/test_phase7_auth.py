"""Tests for User Accounts & Authentication (Phase 7 - Step 10)."""

import os
import tempfile
import pytest

from src.database.connection import get_connection, init_db
from src.database.seed import seed_database
from src.services.auth_service import (
    register_user,
    authenticate_user,
    get_user_by_id,
    get_user_by_email,
    update_user_profile,
    change_password,
    hash_password,
    verify_password,
    normalize_email,
)


@pytest.fixture
def p7_auth_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_p7_01_successful_registration(p7_auth_db):
    """Verify standard user registration succeeds and creates an active user record."""
    success, msg, user = register_user(
        email="shopper@example.com",
        password="secretpassword123",
        display_name="Alex Shopper",
        custom_path=p7_auth_db,
    )
    assert success is True
    assert user is not None
    assert user.id > 0
    assert user.display_name == "Alex Shopper"
    assert user.email == "shopper@example.com"
    assert user.is_active is True
    assert "registered successfully" in msg.lower()


def test_p7_02_duplicate_email_rejection(p7_auth_db):
    """Verify attempting to register with an already registered email is rejected."""
    ok1, _, user1 = register_user(
        email="duplicate@example.com",
        password="password1",
        display_name="First User",
        custom_path=p7_auth_db,
    )
    assert ok1 is True

    # Same email, different case
    ok2, msg2, user2 = register_user(
        email="DUPLICATE@EXAMPLE.COM",
        password="password2",
        display_name="Second User",
        custom_path=p7_auth_db,
    )
    assert ok2 is False
    assert user2 is None
    assert "already exists" in msg2.lower()


def test_p7_03_email_normalization(p7_auth_db):
    """Verify emails are normalized with lowercase and stripped whitespace."""
    raw_email = "  Shopper.Name@DOMAIN.COM  "
    normalized = normalize_email(raw_email)
    assert normalized == "shopper.name@domain.com"

    ok, _, user = register_user(
        email=raw_email,
        password="securepassword123",
        display_name="Normalize Test",
        custom_path=p7_auth_db,
    )
    assert ok is True
    assert user.email == "shopper.name@domain.com"

    # Can authenticate using different case
    auth_ok, _, auth_user = authenticate_user(
        email="SHOPPER.NAME@domain.com",
        password="securepassword123",
        custom_path=p7_auth_db,
    )
    assert auth_ok is True
    assert auth_user.id == user.id


def test_p7_04_successful_login(p7_auth_db):
    """Verify authenticated login succeeds with valid credentials."""
    register_user(
        email="login.test@example.com",
        password="correct_password_42",
        display_name="Login Tester",
        custom_path=p7_auth_db,
    )

    success, msg, user = authenticate_user(
        email="login.test@example.com",
        password="correct_password_42",
        custom_path=p7_auth_db,
    )
    assert success is True
    assert user is not None
    assert user.display_name == "Login Tester"
    assert "successful" in msg.lower()


def test_p7_05_invalid_password_rejection(p7_auth_db):
    """Verify login fails with wrong password without revealing account presence."""
    register_user(
        email="secure.user@example.com",
        password="actual_password",
        display_name="Sec User",
        custom_path=p7_auth_db,
    )

    success, msg, user = authenticate_user(
        email="secure.user@example.com",
        password="WRONG_password",
        custom_path=p7_auth_db,
    )
    assert success is False
    assert user is None
    assert "invalid email address or password" in msg.lower()


def test_p7_06_unknown_account_rejection(p7_auth_db):
    """Verify non-existent account login is rejected with generic error."""
    success, msg, user = authenticate_user(
        email="nonexistent.ghost@example.com",
        password="some_random_password",
        custom_path=p7_auth_db,
    )
    assert success is False
    assert user is None
    assert "invalid email address or password" in msg.lower()


def test_p7_07_passwords_not_stored_plaintext(p7_auth_db):
    """Verify password hashing stores salted PBKDF2 hash, not plaintext."""
    raw_pwd = "MySuperSecretPlaintextPassword!"
    _, _, user = register_user(
        email="crypto.check@example.com",
        password=raw_pwd,
        display_name="Crypto Auditor",
        custom_path=p7_auth_db,
    )

    with get_connection(p7_auth_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user.id,))
        stored_hash = cursor.fetchone()["password_hash"]

    # Plaintext must never appear in database
    assert raw_pwd not in stored_hash
    assert stored_hash.startswith("pbkdf2:sha256:260000$")
    assert verify_password(raw_pwd, stored_hash) is True
    assert verify_password("FakePassword", stored_hash) is False


def test_p7_08_profile_update_and_password_change(p7_auth_db):
    """Verify user can update display name and change password with verification."""
    _, _, user = register_user(
        email="change.me@example.com",
        password="old_password_123",
        display_name="Old Name",
        custom_path=p7_auth_db,
    )

    # 1. Update display name
    up_ok, _ = update_user_profile(user.id, "New Brand Name", custom_path=p7_auth_db)
    assert up_ok is True
    refreshed = get_user_by_id(user.id, custom_path=p7_auth_db)
    assert refreshed.display_name == "New Brand Name"

    # 2. Reject password change with incorrect old password
    cp_fail, fail_msg = change_password(user.id, "wrong_old_pwd", "new_password_456", custom_path=p7_auth_db)
    assert cp_fail is False
    assert "incorrect" in fail_msg.lower()

    # 3. Successful password change
    cp_ok, _ = change_password(user.id, "old_password_123", "new_password_456", custom_path=p7_auth_db)
    assert cp_ok is True

    # 4. Old password no longer works, new password does
    old_auth, _, _ = authenticate_user("change.me@example.com", "old_password_123", custom_path=p7_auth_db)
    assert old_auth is False
    new_auth, _, _ = authenticate_user("change.me@example.com", "new_password_456", custom_path=p7_auth_db)
    assert new_auth is True

