#!/usr/bin/env python3
"""Validate the Trivy exception file.

Rules (docs/03-security-policy.md, "Exceptions"):
  - every entry has id, statement and expired_at (yyyy-mm-dd)
  - an id is a single identifier, no wildcards
  - no entry is already expired
  - expired_at is at most 30 days after the commit date
Uses `yq` (preinstalled on GitHub-hosted Ubuntu runners) to read YAML.
Environment overrides for testing: TODAY, COMMIT_DATE (yyyy-mm-dd).
"""
import datetime
import json
import os
import subprocess
import sys

MAX_DAYS = 30
SECTIONS = ("vulnerabilities", "misconfigurations", "secrets", "licenses")


def parse_date(value, what):
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        sys.exit(f"::error::{what}: '{value}' is not a yyyy-mm-dd date")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else ".trivyignore.yaml"
    raw = subprocess.run(["yq", "-o=json", ".", path], check=True, capture_output=True, text=True).stdout
    doc = json.loads(raw) or {}
    today = parse_date(os.environ.get("TODAY") or datetime.date.today().isoformat(), "TODAY")
    commit_date = parse_date(
        os.environ.get("COMMIT_DATE")
        or subprocess.run(["git", "log", "-1", "--format=%cs"], check=True, capture_output=True, text=True).stdout.strip(),
        "commit date",
    )
    limit = commit_date + datetime.timedelta(days=MAX_DAYS)

    errors = []
    count = 0
    for key in doc:
        if key not in SECTIONS:
            errors.append(f"unknown top-level key '{key}'")
    for section in SECTIONS:
        for i, entry in enumerate(doc.get(section) or []):
            count += 1
            label = f"{section}[{i}] {entry.get('id', '?')}"
            ident = str(entry.get("id") or "")
            if not ident:
                errors.append(f"{label}: missing id")
            elif any(c in ident for c in "*?[] ,"):
                errors.append(f"{label}: id must be one identifier, no wildcards")
            if not str(entry.get("statement") or "").strip():
                errors.append(f"{label}: missing statement")
            if not entry.get("expired_at"):
                errors.append(f"{label}: missing expired_at")
                continue
            expires = parse_date(entry["expired_at"], label)
            if expires < today:
                errors.append(f"{label}: expired on {expires} (today is {today})")
            if expires > limit:
                errors.append(
                    f"{label}: expired_at {expires} is more than {MAX_DAYS} days after commit date {commit_date} (max {limit})"
                )

    if errors:
        for e in errors:
            print(f"::error file={path}::{e}")
        sys.exit(1)
    print(f"{path}: {count} exception(s), all valid (commit date {commit_date}, today {today})")


if __name__ == "__main__":
    main()
