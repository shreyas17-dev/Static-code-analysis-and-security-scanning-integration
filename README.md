# Static Code Analysis & Security Scanning — Team Project
Owner: Person 4 (Docs / QA Lead) — compiled from all members' work

## Team & Responsibilities

| Member | Role | Deliverables |
|---|---|---|
| 1 | Application Developer | `src/db_connector.py` (vulnerable), `src/db_connector_fixed.py` (patched) |
| 2 | Security Engineer | `.gitleaks.toml`, `.bandit`, `docs/security-scan-demo.md` (failing scan) |
| 3 | DevOps / CI Engineer | `.github/workflows/security-scan.yml`, `requirements.txt`, `tests/` |
| 4 | Docs / QA Lead | This README, final report, verifying the passing scan |

## Repo layout
```
.
├── .github/workflows/security-scan.yml   # CI: Gitleaks + Bandit + tests
├── .gitleaks.toml                        # secret scanner config
├── .bandit                               # SAST config
├── requirements.txt
├── src/
│   ├── db_connector.py                   # intentionally vulnerable (demo)
│   └── db_connector_fixed.py             # patched version
├── tests/
│   └── test_db_connector.py
└── docs/
    └── security-scan-demo.md             # failing-scan output + tool research
```

## How to reproduce the demo

1. **Failing scan** (on `db_connector.py`):
   ```bash
   pip install bandit
   bandit -r src/ -f screen
   gitleaks detect --source=.
   ```
   Both exit non-zero — see `docs/security-scan-demo.md` for captured output.

2. **Push to GitHub** → `.github/workflows/security-scan.yml` runs automatically
   and the job fails, blocking the PR.

3. **Apply the fix**: swap references from `db_connector.py` to
   `db_connector_fixed.py` (or replace its contents), which removes every
   flagged issue — parameterized SQL, bcrypt hashing, JSON instead of pickle,
   secrets from environment variables, no `eval()`.

4. **Re-run the pipeline** → job passes, `tests/` also run and pass.

## Sequence for the live demo
1. Show `db_connector.py` and point out the 5 anti-patterns.
2. Run Bandit + Gitleaks locally → show red/failed output with severities and line numbers.
3. Push → show the GitHub Actions job failing in red.
4. Swap in the fixed file, push again → show the job passing in green.
