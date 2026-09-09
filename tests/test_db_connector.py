"""
tests/test_db_connector.py

Basic build/sanity checks for the fixed application code.
Owner: Person 3 (DevOps / CI Engineer)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db_connector import hash_password, verify_password, load_user_session


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_wrong_password_fails_verification():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_password_hash_is_not_plaintext():
    hashed = hash_password("mypassword")
    assert "mypassword" not in hashed


def test_load_user_session_parses_json():
    session = load_user_session('{"user_id": 42, "role": "member"}')
    assert session["user_id"] == 42
    assert session["role"] == "member"
