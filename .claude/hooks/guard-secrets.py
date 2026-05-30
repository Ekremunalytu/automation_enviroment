#!/usr/bin/env python3
"""PreToolUse(Bash) guard for Claude Code: block shell access to real secrets.

Permission `deny` rules only cover the Read/Edit/Write tools, so a plain
`cat .env` would slip through. This hook closes that gap for the Bash tool by
blocking shell commands that touch real secrets: the repo-root .env (and
variants), a secrets/ tree, private keys / certs, and the operator's REAL home
credential files (~/.ssh, ~/.aws, ~/.npmrc, ...). It blocks by exiting 2
(Claude Code surfaces stderr and cancels the call).

NOTE: remote git/PR ops (git push, gh pr merge, ...) are intentionally NOT
blocked here — they are handled by `permissions.ask` in settings.json, which
prompts for approval each time instead of hard-blocking.

HONEYPOT CARVE-OUT: this project seeds a FAKE $HOME full of decoy credentials
(executor/flows/playwright/workspace/seed_*.py) to bait malware. Those decoys
must stay readable, so any path that looks like the decoy/sandbox/workspace
environment is EXEMPT.

Fails OPEN on unexpected input (parse error -> allow) so a bug here can never
wedge the shell; the settings.json deny rules remain as a second layer.
"""

import json
import re
import sys

# --- env files: .env, .env.local, prod.env ... but NOT safe templates -------
_ENV_BASENAME = re.compile(r"^(?:\.env(?:\.[\w-]+)?|[\w.-]+\.env)$", re.IGNORECASE)
_SAFE_ENV_SUFFIX = re.compile(
    r"\.(?:example|sample|template|tmpl|dist|default|md|txt)$", re.IGNORECASE
)

_KEY_EXT = re.compile(
    r"\.(?:pem|key|p12|pfx|keystore|jks|kdbx|asc|ppk)$", re.IGNORECASE
)
_SSH_KEY = re.compile(r"(?:^|/)id_(?:rsa|dsa|ecdsa|ed25519)$", re.IGNORECASE)
_CRED_FILE = re.compile(
    r"(?:^|/)(?:\.git-credentials|\.netrc|\.pgpass|\.npmrc|\.pypirc|"
    r"credentials(?:\.json)?)$",
    re.IGNORECASE,
)
# Real operator home credential dirs (the decoys live elsewhere, see carve-out).
_HOME_SECRET = re.compile(
    r"(?:^|/)(?:~|\$HOME)?/?\.(?:ssh|aws|gnupg|kube|docker/config\.json|"
    r"config/gcloud)(?:/|$)",
    re.IGNORECASE,
)

# Honeypot / decoy / sandbox markers — anything here is FAKE bait, leave it open.
_EXEMPT = (
    "sandbox",
    "workspace/",
    "honeypot",
    "decoy",
    "canary",
    "fixture",
    "/malicious/",
    "seedcorpus",
)

# Strip shell punctuation that commonly hugs an argument.
_STRIP = "\"'`;|&()<>{}$"


def classify_secret(token: str):
    """Return a human label if the token references a real secret, else None."""
    t = token.strip().strip(_STRIP)
    if not t:
        return None
    low = t.lower()
    # Honeypot carve-out: decoy/sandbox/workspace bait is always allowed.
    if any(marker in low for marker in _EXEMPT):
        return None
    base = t.rsplit("/", 1)[-1]
    if _ENV_BASENAME.match(base) and not _SAFE_ENV_SUFFIX.search(base):
        return ".env / environment secret file"
    if t == "secrets" or "secrets/" in low:
        return "secrets/ path"
    if _HOME_SECRET.search(t):
        return "home credential dir (~/.ssh, ~/.aws, ...)"
    if _KEY_EXT.search(base):
        return "private key / certificate file"
    if _SSH_KEY.search(t):
        return "ssh private key"
    if _CRED_FILE.search(t):
        return "credentials file"
    return None


def block(reason: str) -> None:
    print(f"[guard-secrets] BLOCKED: {reason}", file=sys.stderr)
    print(
        "Reading real .env/secret/key/credential files via the shell is "
        "forbidden. Decoy/honeypot fixtures (sandbox/, workspace/, honeypot, ...) "
        "are exempt. If this is a legitimate non-secret target, run it yourself "
        "or adjust .claude/hooks/guard-secrets.py / .claude/settings.json.",
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd.strip():
        sys.exit(0)

    # env-dumping commands (leak secret env vars).
    if re.search(r"(?:^|[\s;|&(])printenv\b", cmd):
        block("environment dump (printenv)")
    if re.search(r"(?:^|[\s;|&(])env(?:\s*(?:$|\||;|&))", cmd):
        block("environment dump (env)")

    # any token that points at a real secret file.
    for token in re.split(r"\s+", cmd):
        label = classify_secret(token)
        if label:
            block(f"shell access to {label} ({token.strip(_STRIP)})")

    sys.exit(0)


if __name__ == "__main__":
    main()
