import os
import sqlite3
import json
import bcrypt

# --- Fix 1: secrets pulled from environment, never hardcoded ---
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD_HASH = os.environ.get("DB_PASSWORD_HASH")  # store a hash, not plaintext
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
API_TOKEN = os.environ.get("API_TOKEN")


def connect_to_db():
    """Connect to the database. Credentials come from environment/secrets manager."""
    conn = sqlite3.connect("app.db")
    return conn


def get_user(conn, username):
    """Fix 2: parameterized query prevents SQL injection."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


def hash_password(password: str) -> str:
    """Fix 3: bcrypt (salted, slow hash) instead of MD5."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def load_user_session(data: str):
    """Fix 4: json.loads instead of pickle.loads — no arbitrary code execution risk."""
    return json.loads(data)


def debug_login(username: str, password: str) -> bool:
    """Fix 5: no eval(); constant-time-safe comparison against a stored hash."""
    if username == DB_USER and DB_PASSWORD_HASH and verify_password(password, DB_PASSWORD_HASH):
        return True
    return False