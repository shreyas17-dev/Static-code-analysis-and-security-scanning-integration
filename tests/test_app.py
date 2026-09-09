"""Functional tests for the Secure Code Scanner application.

These tests check that the application behaves correctly. They say nothing
about whether the code is secure - that is the Gitleaks job's responsibility.
"""

import pytest

import app
import auth

# A throwaway key used only inside these tests. The real key is supplied by
# auth.get_api_key(), which each test replaces with this value.
TEST_KEY = "unit-test-key"


@pytest.fixture(autouse=True)
def fixed_api_key(monkeypatch):
    """Make every test run against a known, predictable API key."""
    monkeypatch.setattr(auth, "get_api_key", lambda: TEST_KEY)


def test_scan_text_finds_risky_calls():
    assert app.scan_text("value = eval(user_input)") == ["eval("]


def test_scan_text_reports_every_match_sorted():
    source = "os.system(cmd)\nexec(payload)\n"
    assert app.scan_text(source) == ["exec(", "os.system("]


def test_scan_text_returns_nothing_for_clean_code():
    assert app.scan_text("total = a + b\n") == []


def test_scan_file_reads_from_disk(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text("import pickle\npickle.loads(blob)\n", encoding="utf-8")
    assert app.scan_file(str(sample)) == ["pickle.loads("]


def test_run_accepts_the_correct_key():
    assert app.run(TEST_KEY, "eval(x)") == ["eval("]


def test_run_rejects_a_wrong_key():
    with pytest.raises(PermissionError):
        app.run("wrong-key", "eval(x)")


def test_run_rejects_a_missing_key():
    with pytest.raises(PermissionError):
        app.run("", "eval(x)")


def test_authorisation_fails_when_no_key_is_configured(monkeypatch):
    monkeypatch.setattr(auth, "get_api_key", lambda: None)
    assert auth.is_authorised(TEST_KEY) is False


def test_main_reports_a_missing_file_without_crashing(capsys):
    assert app.main(["app.py", "no-such-file.py"]) == 1
    assert "Could not read" in capsys.readouterr().out
