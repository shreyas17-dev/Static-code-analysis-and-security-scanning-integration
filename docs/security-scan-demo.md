# Scanner Selection & Failing-Scan Demo
Owner: Person 2 (Security Engineer)

## Tool selection

| Tool | Type | Why chosen |
|---|---|---|
| **Gitleaks** | Secret scanner | Free, open-source, fast, scans full git history (not just working tree), native GitHub Action available, low false-positive rate on common credential formats (AWS keys, GitHub PATs, etc). |
| **Bandit** | SAST (Python) | Free, open-source, purpose-built for Python (our stack), detects SQLi, weak crypto, unsafe eval/pickle, with severity + confidence scoring and exact line numbers. |

**Alternatives considered:** TruffleHog (secrets — more noisy on entropy-based
detection than Gitleaks), SonarQube Community (broader but heavier to self-host
for a class project), CodeQL (powerful but steeper setup, GitHub-only).

## Demonstrating a FAILED scan

Run against Person 1's vulnerable `src/db_connector.py`:

```bash
pip install bandit
bandit -r src/ -f screen
```

### Actual output captured

```
Run started: <timestamp>

Test results:
>> Issue: [B403:blacklist] Consider possible security implications associated
   with pickle module.
   Severity: Low   Confidence: High
   Location: src/db_connector.py:11:0

>> Issue: [B105:hardcoded_password_string] Possible hardcoded password:
   'SuperSecret123!'
   Severity: Low   Confidence: Medium
   Location: src/db_connector.py:15:14

>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector
   through string-based query construction.
   Severity: Medium   Confidence: Low
   Location: src/db_connector.py:30:12

>> Issue: [B324:hashlib] Use of weak MD5 hash for security.
   Severity: High   Confidence: High
   Location: src/db_connector.py:37:11

>> Issue: [B301:blacklist] Pickle and modules that wrap it can be unsafe when
   used to deserialize untrusted data.
   Severity: Medium   Confidence: High
   Location: src/db_connector.py:42:11

>> Issue: [B307:blacklist] Use of possibly insecure function - consider
   using safer ast.literal_eval.
   Severity: Medium   Confidence: High
   Location: src/db_connector.py:48:8

Total issues (by severity): Low: 4  Medium: 3  High: 1
```

```bash
gitleaks detect --source=. -v
```

```
Finding:     API_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
RuleID:      github-pat
File:        src/db_connector.py
Line:        18
WRN leaks found: 2
```

**Exit code: non-zero → this is what makes the CI job fail (see Person 3's workflow).**
