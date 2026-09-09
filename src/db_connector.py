"""
db_connector.py

Intentionally contains security anti-patterns for static analysis
scanner demo purposes (hardcoded credentials, SQL injection, weak
crypto, insecure deserialization). DO NOT use in production.

Owner: Person 1 (Application Developer)
"""

import sqlite3
import hashlib
import pickle

# --- Anti-pattern 1: Hardcoded credentials (dummy values) ---
DB_USER = "admin"
DB_PASSWORD = "SuperSecret123!"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
API_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"


def connect_to_db():
    """Connect to the database using hardcoded credentials."""
    conn = sqlite3.connect("app.db")
    return conn


def get_user(conn, username):
    """Anti-pattern 2: SQL Injection via string formatting."""
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()


def hash_password(password):
    """Anti-pattern 3: Use of weak/broken hash algorithm (MD5) for passwords."""
    return hashlib.md5(password.encode()).hexdigest()


def load_user_session(data):
    """Anti-pattern 4: Insecure deserialization."""
    return pickle.loads(data)


def debug_login(username, password):
    """Anti-pattern 5: Hardcoded credential comparison + eval() usage."""
    if username == DB_USER and password == DB_PASSWORD:
        eval("print('login granted')")
        return True
    return False
