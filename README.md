# Secure Code Scanner

Static code analysis and security scanning integration for a CI/CD pipeline.

---

## 1. Project overview

Secure Code Scanner is a small Python application wired into a GitHub Actions
pipeline that runs two independent gates on every push and every pull request:

| Gate | Tool | Question it answers |
| --- | --- | --- |
| Application tests | pytest | Does the code do the right thing? |
| Secret scan | Gitleaks | Does the code leak a credential? |

The repository deliberately contains one hardcoded credential so the security
gate can be seen failing, and then seen passing once the credential is moved
out of the source code.

**pytest measures functional correctness. Gitleaks measures secret hygiene.
Neither one makes the application "secure".**

---

## 2. Problem statement

Hardcoded credentials are one of the most common and most damaging defects in
real software. A key committed to Git stays in the repository history even
after it is deleted from the working copy, and anyone who can clone the
repository can read it.

Code review alone does not catch this reliably. A reviewer reading a large diff
will miss a single line that assigns a key to a variable. The check has to be
automated and it has to block the merge.

---

## 3. Objective

Demonstrate a working DevSecOps feedback loop:

```
Python application
    -> intentional fake hardcoded credential
    -> push to GitHub
    -> GitHub Actions runs
    -> Gitleaks detects the credential
    -> workflow fails
    -> developer removes the credential
    -> push again
    -> Gitleaks passes, tests pass
    -> workflow succeeds
```

---

## 4. Technologies used

| Technology | Version used here | Role |
| --- | --- | --- |
| Python | 3.12 in CI | Application language |
| pytest | 8.x | Test runner |
| GitHub Actions | n/a | CI pipeline |
| Gitleaks | 8.30.1 | Secret detection |
| gitleaks/gitleaks-action | v3 | Runs Gitleaks inside Actions |
| actions/checkout | v6 | Clones the repository |
| actions/setup-python | v6 | Installs Python |

The application itself uses only the Python standard library. There is no
framework, no database, no frontend and no container.

`actions/checkout@v6` and `actions/setup-python@v6` are pinned deliberately.
v7 of both exists, but v6 is the pairing the Gitleaks Action v3 documentation
specifies, and nothing in v7 is needed here.

---

## 5. Architecture and workflow

```
 developer
    |
    | git push  /  open pull request
    v
 GitHub Actions  (.github/workflows/security.yml)
    |
    +--- job: tests        -> checkout -> setup-python -> pip install -> pytest
    |
    +--- job: secret-scan  -> checkout (full history) -> gitleaks-action@v3
                                     |
                                     +-- reads .gitleaks.toml
                                     +-- exit code 2 when a secret is found
    |
    v
 red or green check on the commit / pull request
```

The two jobs are independent and run in parallel. If either one fails the whole
run is marked failed, so a merge cannot be waved through on the strength of
green tests alone.

---

## 6. Project structure

```
Static-code-analysis-and-security-scanning-integration/
├── app.py                        # the scanner application
├── auth.py                       # API key handling + the deliberate vulnerability
├── requirements.txt              # pytest
├── pytest.ini                    # lets tests/ import app.py and auth.py
├── .gitleaks.toml                # Gitleaks ruleset for this project
├── .gitignore
├── README.md
├── tests/
│   └── test_app.py               # 9 pytest tests
└── .github/
    └── workflows/
        └── security.yml          # the CI pipeline
```

---

## 7. The Python application

`app.py` is a miniature static analysis tool. It reads a Python file and
reports the risky calls it contains.

| Function | Purpose |
| --- | --- |
| `scan_text(text)` | Returns the risky patterns found in a string, sorted |
| `scan_file(path)` | Reads a file and scans its contents |
| `run(api_key, text)` | Checks authorisation, then scans |
| `main(argv)` | Command line entry point |

The patterns it looks for are `eval(`, `exec(`, `os.system(` and
`pickle.loads(`, all of which can execute attacker-controlled input.

`auth.py` holds the credential handling:

| Function | Purpose |
| --- | --- |
| `get_api_key()` | Returns the key the scanner expects |
| `is_authorised(api_key)` | Constant-time comparison of the supplied key |

Run it:

```bash
python app.py some_file.py
```

Exit code 0 means nothing risky was found, 1 means something was.

---

## 8. What Gitleaks is

Gitleaks is an open source secret scanner. It walks either the working tree or
the commit history of a Git repository and matches the content against a
ruleset of roughly two hundred rules covering AWS keys, GitHub tokens, Slack
tokens, Stripe keys, private keys and generic high-entropy strings assigned to
variables named like credentials.

When it finds something it prints the rule that matched, the file, the line and
a fingerprint, and exits with a non-zero status. That non-zero exit is what
fails the pipeline.

---

## 9. Why Gitleaks was selected

* It targets exactly the defect this project is about: committed credentials.
* It scans Git history, not just the current files, which is the difference
  between finding a leak and missing one that was "deleted" in a later commit.
* It has an official, maintained GitHub Action, so no custom scripting.
* It is free for repositories owned by a personal account. A licence key is
  only needed for repositories owned by a GitHub organisation.
* Its output names a rule, a file and a line, which is short enough to read
  aloud during a demonstration.

Gitleaks is not a general-purpose static analysis tool. It does not look for
SQL injection or unsafe deserialisation. It looks for secrets.

---

## 10. Gitleaks configuration

`.gitleaks.toml` at the repository root does two things.

First, it keeps every rule Gitleaks ships with:

```toml
[extend]
useDefault = true
```

Second, it adds one project-specific rule that matches the shape of the
assignment rather than the content of the value.

**Why the extra rule exists.** The built-in `generic-api-key` rule combines a
keyword match with an entropy threshold and a large stopword list. Values
containing words such as `demo`, `fake`, `test` or `example` are deliberately
ignored, because in real projects those are usually placeholders rather than
live credentials. That behaviour was confirmed directly against Gitleaks
8.30.1. Both of the following produced **no finding at all**:

```python
API_KEY = "dummy-secret-key"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
```

So a demonstration that relies on a value which merely *looks* fake is
fragile. The custom rule removes that fragility, and it is restricted to `.py`
files so that this README can discuss the problem in prose without tripping the
scanner.

The workflow points at the configuration file explicitly through the
`GITLEAKS_CONFIG` environment variable rather than relying on auto-discovery.

---

## 11. The deliberate vulnerability (KAN-5)

`auth.py` assigns a 32-character placeholder string to `SCANNER_API_KEY` at
module level. The value is random filler. It is not a real credential, it
matches no real provider's key format, it belongs to no service and it grants
access to nothing. It exists only so the security gate has something to detect.

Two separate rules catch it, both verified locally:

* `hardcoded-scanner-api-key` — the project rule, matches the assignment shape.
* `generic-api-key` — the built-in rule, matches on entropy 5.0 with the
  `api_key` keyword nearby.

Either one alone is enough to fail the build.

---

## 12. Expected failed scan (KAN-11)

Actual output from Gitleaks 8.30.1 run against this repository, with the secret
value redacted:

```
Finding:     SCANNER_API_KEY = "REDACTED"
RuleID:      hardcoded-scanner-api-key
File:        auth.py
Line:        19
Fingerprint: <commit-sha>:auth.py:hardcoded-scanner-api-key:19

WRN leaks found: 1
```

Exit code: **2**. The `secret-scan` job fails and the workflow run is red.

Gitleaks does not assign a severity to its findings, so no severity is quoted
here.

---

## 13. The fix (KAN-12)

Replace the hardcoded assignment in `auth.py` with an environment variable
lookup:

```python
import os

API_KEY_VARIABLE = "SCANNER_API_KEY"

def get_api_key():
    return os.getenv(API_KEY_VARIABLE)
```

The key is then supplied at run time and never written to the repository:

```bash
export SCANNER_API_KEY="any-key-you-choose"     # macOS / Linux
```

```powershell
$env:SCANNER_API_KEY = "any-key-you-choose"     # Windows PowerShell
```

The application keeps working. The tests keep passing, because they replace
`auth.get_api_key` with a known value rather than depending on how the key is
stored.

**Before:** credential in source code, therefore in Git history forever, and
Gitleaks fails the build.

**After:** credential in the environment, nothing to find in the repository,
and Gitleaks passes.

One honest caveat. Moving a key to an environment variable does not make an
application secure. It removes one specific, very common defect. A key that has
already been committed must also be rotated, because it stays readable in the
repository history.

---

## 14. Expected successful scan (KAN-13)

After the fix, the same scan produces:

```
INF no leaks found
```

Exit code: **0**. Both jobs are green.

---

## 15. GitHub Actions workflow

`.github/workflows/security.yml`:

* **Triggers** on `push` and on `pull_request`.
* **Permissions** default to `contents: read` for the whole workflow. Only the
  `secret-scan` job adds `pull-requests: write`, which Gitleaks needs in order
  to comment on the offending line of a pull request.
* **Job `tests`** checks out the code, installs Python 3.12, installs
  `requirements.txt` and runs `pytest -v`.
* **Job `secret-scan`** checks out with `fetch-depth: 0` so the full history is
  available, then runs `gitleaks/gitleaks-action@v3`.
* `GITHUB_TOKEN` is the token GitHub creates automatically for every run. The
  Gitleaks Action needs it to list the commits in a pull request. Nobody has to
  create or store it.
* `GITLEAKS_LICENSE` is **not** set, and is not needed, because this repository
  belongs to a personal account rather than a GitHub organisation.

No real secret appears anywhere in the workflow file.

### What Gitleaks actually scans, per event

This matters for the demonstration. It was read from the Action's source and
then reproduced locally:

| Event | Range scanned |
| --- | --- |
| `push` of a single commit | that one commit |
| `push` of several commits | the commits in that push |
| `pull_request` | **every commit in the pull request** |

So a push containing only the fix passes, but a pull request whose branch still
contains the earlier vulnerable commit will keep failing, because the secret
genuinely is still in that branch's history. Section 22 explains how to handle
that.

---

## 16. Testing

`tests/test_app.py` contains nine tests. They cover pattern detection, reading
from disk, the authorisation check for a correct, a wrong and a missing key,
the case where no key is configured at all, and the command line error path.

An autouse fixture replaces `auth.get_api_key` with a throwaway value, so the
tests are deterministic and pass identically before and after the KAN-12 fix.
No credential of any kind is stored in the test file.

```bash
pytest -v
```

They run in well under a second.

---

## 17. Local setup

```bash
git clone <repository-url>
cd Static-code-analysis-and-security-scanning-integration

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pytest -v
python app.py app.py
```

On Windows PowerShell the activation line is `.venv\Scripts\Activate.ps1`.

To run Gitleaks locally, download the binary for your platform from
<https://github.com/gitleaks/gitleaks/releases> and run:

```bash
gitleaks dir . --config .gitleaks.toml -v        # scan the current files
gitleaks detect --config .gitleaks.toml -v       # scan the Git history
```

---

## 18. Reproducing the failed scan

1. Confirm `auth.py` still contains the hardcoded `SCANNER_API_KEY`.
2. Commit and push the branch.
3. Open the Actions tab. The `Security` run appears.
4. `Application tests (pytest)` passes. `Secret scan (Gitleaks)` fails.
5. Open the failing job and read the finding: rule, file, line, fingerprint.
6. The SARIF report is attached to the run as the `gitleaks-results.sarif`
   artifact.

The same failure locally:

```bash
gitleaks dir . --config .gitleaks.toml -v --exit-code 2
echo $?      # 2
```

---

## 19. Reproducing the successful scan

1. Apply the KAN-12 change to `auth.py`.
2. Commit and push.
3. A new `Security` run starts. Both jobs pass.

Locally:

```bash
gitleaks dir . --config .gitleaks.toml -v
# INF no leaks found
```

---

## 20. Jira traceability

The Jira project key is **KAN**. There is no Jira API integration in this
repository and no automation between Jira and GitHub. The link is by
convention: the issue key appears in the branch name, the commit messages and
the pull request title, which is what lets a reader trace a line of code back
to the requirement that asked for it.

| Issue | Title | Where it lives in the repository |
| --- | --- | --- |
| KAN-4 | Set up Python application | `app.py`, `auth.py`, `requirements.txt`, `pytest.ini` |
| KAN-5 | Add intentional dummy vulnerability | the hardcoded `SCANNER_API_KEY` in `auth.py` |
| KAN-6 | Select and research security scanner | sections 8 and 9 of this README |
| KAN-7 | Configure security scanner | `.gitleaks.toml` |
| KAN-8 | Create GitHub Actions security workflow | `.github/workflows/security.yml` |
| KAN-9 | Add tests and build checks | `tests/test_app.py` and the `tests` job |
| KAN-10 | Set up Jira-GitHub workflow | this section and section 21 |
| KAN-11 | Demonstrate failed security scan | section 18, the red Actions run |
| KAN-12 | Fix detected security vulnerability | section 13 |
| KAN-13 | Verify successful security scan | section 19, the green Actions run |

---

## 21. Git branch and pull request workflow

```
Jira issue (KAN-n)
    -> git branch named after the issue
    -> write code
    -> commit, with the issue key in the message
    -> push
    -> open a pull request
    -> code review
    -> GitHub Actions runs tests and the secret scan
    -> merge once both are green
```

Branch naming used here: `feature/KAN-4-to-KAN-13-full-project`.

Commit message convention: `KAN-5: add deliberate hardcoded credential`.

The pull request targets `main`. `main` is never committed to directly.

---

## 22. Pull request behaviour after the fix

Because Gitleaks scans **every commit in a pull request**, a branch whose
history contains the vulnerable commit keeps failing the secret scan even after
the fix commit is added. That is correct behaviour rather than a bug: the
secret really is still in that branch's history.

Pick one of these before merging. Both were tested.

**Option A, record the finding as remediated.** This is what a real team does.
Create a `.gitleaksignore` file at the repository root containing the
fingerprint copied verbatim from the failed run:

```
# Finding reviewed and remediated in KAN-12. The credential was never real.
<commit-sha>:auth.py:hardcoded-scanner-api-key:19
```

Commit it alongside the fix. The pull request then passes. In a real incident
the key would also be rotated, because the ignore file suppresses the alert
without removing the secret from history.

**Option B, merge from a clean branch.** Branch fresh from `main` after the
fix, apply only the fixed files, and open the pull request from there. The
vulnerable commit never enters the pull request.

Option A is the better thing to show a professor, because it makes the point
that deleting a secret from a file does not delete it from history.

---

## 23. Classroom demonstration procedure

**Stage 1, the failure (KAN-11)**

1. Show `auth.py` and point at the hardcoded `SCANNER_API_KEY` line.
2. Show `.gitleaks.toml` and explain the two sources of rules.
3. Push the branch.
4. Open the Actions tab and let the run finish.
5. Show `Application tests (pytest)` green: the code is functionally correct.
6. Show `Secret scan (Gitleaks)` red.
7. Open the job log and read out the rule name, file, line and fingerprint.
8. Make the point: the tests passed, so tests alone would have let this merge.

**Stage 2, the fix (KAN-12 and KAN-13)**

1. Edit `auth.py` to read the key from the environment.
2. Show that `pytest -v` still passes locally.
3. Commit and push.
4. Show the new run with both jobs green.
5. Close by saying what this does and does not prove. It proves the credential
   is no longer in the source code. It does not prove the application is
   secure, and a real leaked key would still need to be rotated.

---

## Security note

The only credential-like value in this repository is the deliberate
demonstration placeholder in `auth.py`. It is not a real key for any service.
No real API key, password, token or cloud credential appears anywhere in this
repository, including in this README, the workflow file and the tests.
