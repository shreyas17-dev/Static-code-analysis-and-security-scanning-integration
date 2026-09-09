"""Secure Code Scanner - a very small static analysis demo application.

The application reads a piece of Python source code and reports the risky
function calls it contains. It is deliberately tiny: its only job is to give
the pipeline in .github/workflows/security.yml something real to test and to
scan.
"""

import sys

from auth import is_authorised

# Calls that are commonly flagged by static analysis tools because they can
# execute attacker-controlled input.
RISKY_PATTERNS = ("eval(", "exec(", "os.system(", "pickle.loads(")


def scan_text(text):
    """Return the risky patterns found in ``text``, in alphabetical order."""
    return sorted(pattern for pattern in RISKY_PATTERNS if pattern in text)


def scan_file(path):
    """Return the risky patterns found in the file at ``path``."""
    with open(path, encoding="utf-8") as handle:
        return scan_text(handle.read())


def run(api_key, text):
    """Scan ``text`` on behalf of a caller holding ``api_key``.

    Raises PermissionError when the key is missing or wrong.
    """
    if not is_authorised(api_key):
        raise PermissionError("Invalid API key")
    return scan_text(text)


def main(argv):
    """Command line entry point: ``python app.py <file>``."""
    if len(argv) != 2:
        print("usage: python app.py <file-to-scan>")
        return 1

    try:
        findings = scan_file(argv[1])
    except OSError as error:
        print(f"Could not read {argv[1]}: {error}")
        return 1

    if not findings:
        print(f"No risky patterns found in {argv[1]}")
        return 0

    print(f"{len(findings)} risky pattern(s) found in {argv[1]}:")
    for finding in findings:
        print(f"  - {finding}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
