"""Filesystem workspace helpers (pathlib-based, no Playwright).

Prepares files/directories on disk before VS Code opens so that
workspace-based activation events fire on startup.

Covers activation events: workspaceContains:*, onLanguage:* (preparation)
"""

import shutil
import stat
from pathlib import Path

from language_samples import _LANGUAGE_SAMPLE_FILES, _WORKSPACE_PATTERN_FILES

WORKSPACE_DIR = Path("/workspace")
HOME_DIR = Path("/home/executor")

LANGUAGE_EXTENSIONS: dict[str, str] = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "rust": ".rs",
    "go": ".go",
    "c": ".c",
    "cpp": ".cpp",
    "csharp": ".cs",
    "html": ".html",
    "css": ".css",
    "json": ".json",
    "markdown": ".md",
    "yaml": ".yaml",
    "xml": ".xml",
    "ruby": ".rb",
    "php": ".php",
    "swift": ".swift",
    "kotlin": ".kt",
    "shellscript": ".sh",
}


def create_workspace_file(filename: str, content: str = "") -> Path:
    """Create a file inside the workspace directory."""
    path = WORKSPACE_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def create_workspace_dir(dirname: str) -> Path:
    """Create a directory inside the workspace."""
    path = WORKSPACE_DIR / dirname
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_language_file(language_id: str) -> Path:
    """Create a sample file for a given VS Code language ID.

    Raises KeyError if the language_id is not in LANGUAGE_EXTENSIONS.
    """
    ext = LANGUAGE_EXTENSIONS[language_id]
    return create_workspace_file(f"sample{ext}")


def create_workspace_structure(files: dict[str, str]) -> list[Path]:
    """Create multiple files at once.

    Args:
        files: Mapping of relative path -> file content.

    Returns:
        List of created file paths.
    """
    return [create_workspace_file(name, content) for name, content in files.items()]


def create_bait_files(filenames: list[str]) -> list[Path]:
    """Create empty bait files inside the active workspace."""
    created_files: list[Path] = []
    for name in filenames:
        bait_path = WORKSPACE_DIR / name
        bait_path.parent.mkdir(parents=True, exist_ok=True)
        if not bait_path.exists():
            bait_path.write_text("")
        created_files.append(bait_path)
    return created_files


def clean_workspace() -> None:
    """Remove all contents of the workspace directory."""
    for child in WORKSPACE_DIR.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


# ---------------------------------------------------------------------------
# Honeypot developer environment
# ---------------------------------------------------------------------------
# Realistic fake credentials that malicious extensions would try to exfiltrate.
# All values are canary tokens — obviously fake but formatted correctly.
# ---------------------------------------------------------------------------

_HOME_FILES: dict[str, str] = {
    # --- SSH ---
    ".ssh/id_rsa": """\
EXTRACE_FAKE_OPENSSH_KEY
owner=dev@extrace.io
algorithm=ssh-ed25519
material=this-is-a-canary-not-a-real-private-key
EXTRACE_FAKE_OPENSSH_KEY_END
""",
    ".ssh/id_rsa.pub": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGYUMpVscUadF0F9L0Ktni0psx1Vo2sYwfl/Eo84duRA dev@extrace.io\n",
    ".ssh/config": """\
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa

Host production-server
    HostName 10.0.1.50
    User deploy
    IdentityFile ~/.ssh/id_rsa
    Port 2222
""",
    ".ssh/known_hosts": "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n",
    # --- AWS ---
    ".aws/credentials": """\
[default]
aws_access_key_id = AKIAIOSFODNN7EXTRACE
aws_secret_access_key = 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

[production]
aws_access_key_id = AKIAI44QH8DHBEXTRACE
aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXTRACEKEY
""",
    ".aws/config": """\
[default]
region = eu-west-1
output = json

[profile production]
region = us-east-1
output = json
""",
    # --- Kubernetes ---
    ".kube/config": """\
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://k8s.extrace-internal.io:6443
    certificate-authority-data: LS0tLS1CRUdJTi...FURS0tLS0t
  name: production
contexts:
- context:
    cluster: production
    user: admin
    namespace: default
  name: production
current-context: production
users:
- name: admin
  user:
    token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.extrace-fake-token
""",
    # --- Docker ---
    ".docker/config.json": """\
{
  "auths": {
    "ghcr.io": {
      "auth": "ZXh0cmFjZTpnaHBfZmFrZVRva2VuRm9ySG9uZXlwb3RUZXN0"
    },
    "registry.extrace.io": {
      "auth": "ZGVwbG95OmV4dHJhY2Utc2VjcmV0LXJlZ2lzdHJ5LXBhc3M="
    }
  }
}
""",
    # --- GCP ---
    ".config/gcloud/application_default_credentials.json": """\
{
  "client_id": "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",
  "client_secret": "d-FL95Q19q7MQmFpd7hHD0Ty",
  "refresh_token": "1//0extrace-fake-refresh-token-for-honeypot",
  "type": "authorized_user"
}
""",
    # --- NPM ---
    ".npmrc": """\
//registry.npmjs.org/:_authToken=npm_fakeTokenExtraceHoneypot1234567890
//npm.pkg.github.com/:_authToken=ghp_fakeGitHubPATforExtraceHoneypot99
registry=https://registry.npmjs.org/
""",
    # --- Git global ---
    ".gitconfig": """\
[user]
    name = Ahmet Yilmaz
    email = ahmet.yilmaz@extrace.io
[credential]
    helper = store
[core]
    editor = code --wait
""",
    ".git-credentials": "https://ahmet-yilmaz:ghp_R8nFakePatTokenExtrace7890123456@github.com\n",
    # --- Shell history (juicy commands) ---
    ".bash_history": """\
ssh deploy@10.0.1.50
docker login ghcr.io -u extrace -p ghp_fakeTokenExtrace123
export DATABASE_URL=postgresql://admin:s3cretPa55w0rd@db.extrace.io:5432/production
kubectl get secrets -n production
aws s3 ls s3://extrace-backups/
curl -H "Authorization: Bearer sk-proj-fakeOpenAIkeyExtrace123456" https://api.openai.com/v1/models
scp -i ~/.ssh/id_rsa backup.tar.gz deploy@10.0.1.50:/backups/
mysql -h db.extrace.io -u root -p'Sup3rS3cret!' production
redis-cli -h cache.extrace.io -a 'r3d1s_p@ss_extrace'
STRIPE_SECRET_KEY=sk_live_fakeStripeKeyExtrace123 node server.js
""",
    # --- Python REPL history ---
    ".python_history": """\
import os
os.environ['DATABASE_URL']
import boto3
s3 = boto3.client('s3')
s3.list_buckets()
""",
}

_WORKSPACE_FILES: dict[str, str] = {
    # --- Environment files ---
    ".env": """\
# App Configuration
NODE_ENV=production
PORT=3000

# Database
DATABASE_URL=postgresql://extrace_user:Xk9$mP2vL7nQ@db.extrace.io:5432/extrace_prod
REDIS_URL=redis://:r3d1sP@ssExtrace@cache.extrace.io:6379/0

# Auth & API Keys
JWT_SECRET=extrace-jwt-sup3r-s3cret-k3y-2024-pr0duction
SESSION_SECRET=s3ss10n-k3y-extrace-d0nt-share

# Third-party Services
OPENAI_API_KEY=sk-proj-fakeOpenAIKeyForExtraceHoneypot1234567890abcdef
STRIPE_SECRET_KEY=sk_live_fakeStripeKeyExtrace567890
STRIPE_WEBHOOK_SECRET=whsec_fakeStripeWebhookExtrace123
SENDGRID_API_KEY=SG.fakeExtraceSendGridKey.abcdefghijklmnopqrstuvwxyz012345
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
SENTRY_DSN=https://fakekey@o123456.ingest.sentry.io/1234567

# AWS (duplicated for app use)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXTRACE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXTRACEKEY
AWS_REGION=eu-west-1
S3_BUCKET=extrace-uploads-prod
""",
    ".env.production": """\
DATABASE_URL=postgresql://extrace_prod:Pr0dP@ss!2024@rds.extrace.io:5432/extrace
REDIS_URL=redis://prod-cache.extrace.io:6379/0
API_KEY=extrace-prod-api-key-7f8a9b0c1d2e
""",
    ".env.local": """\
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/extrace_dev
REDIS_URL=redis://localhost:6379/0
DEBUG=true
OPENAI_API_KEY=sk-proj-devTestKeyNotReal1234567890
""",
    # --- Git config ---
    ".git/config": """\
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
[remote "origin"]
    url = git@github.com:extrace-io/extrace-backend.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
    remote = origin
    merge = refs/heads/main
""",
    ".git/HEAD": "ref: refs/heads/main\n",
    # --- Python source code ---
    "src/app.py": """\
from flask import Flask, jsonify
from src.config import Config
from src.database import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/users")
def get_users():
    users = db.session.execute("SELECT * FROM users").fetchall()
    return jsonify([dict(u) for u in users])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
""",
    "src/config.py": """\
import os


class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET", "dev-fallback-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/extrace_dev",
    )
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
""",
    "src/database.py": """\
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_connection_string():
    return "postgresql://extrace_user:Xk9$mP2vL7nQ@db.extrace.io:5432/extrace_prod"
""",
    "src/auth.py": """\
import jwt
import os

JWT_SECRET = os.environ.get("JWT_SECRET", "extrace-jwt-sup3r-s3cret-k3y-2024-pr0duction")
ALGORITHM = "HS256"


def create_token(user_id: int) -> str:
    payload = {"sub": user_id, "iss": "extrace"}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
""",
    "src/payments.py": """\
import stripe
import os

stripe.api_key = os.environ.get(
    "STRIPE_SECRET_KEY", "sk_live_fakeStripeKeyExtrace567890"
)


def create_checkout_session(price_id: str, customer_email: str):
    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        customer_email=customer_email,
        success_url="https://extrace.io/success",
        cancel_url="https://extrace.io/cancel",
    )
""",
    "src/storage.py": """\
import boto3
import os

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION", "eu-west-1"),
)

BUCKET = os.environ.get("S3_BUCKET", "extrace-uploads-prod")


def upload_file(file_path: str, key: str):
    s3.upload_file(file_path, BUCKET, key)
    return f"https://{BUCKET}.s3.amazonaws.com/{key}"
""",
    "src/utils.py": """\
import hashlib
import secrets


def generate_api_key() -> str:
    return f"extrace_{secrets.token_hex(32)}"


def hash_password(password: str, salt: str = "extrace-salt-2024") -> str:
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
""",
    # --- JavaScript / Node.js ---
    "frontend/src/api.js": """\
const API_BASE = process.env.REACT_APP_API_URL || "https://api.extrace.io";

export async function fetchWithAuth(endpoint, options = {}) {
  const token = localStorage.getItem("auth_token");
  return fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
}
""",
    "frontend/.env": """\
REACT_APP_API_URL=https://api.extrace.io
REACT_APP_STRIPE_PK=pk_live_fakeStripePublishableKeyExtrace
REACT_APP_SENTRY_DSN=https://fakekey@o123456.ingest.sentry.io/1234567
""",
    "frontend/package.json": """\
{
  "name": "extrace-frontend",
  "version": "1.2.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@stripe/stripe-js": "^1.54.0",
    "axios": "^1.6.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  }
}
""",
    # --- Docker & Infra ---
    "docker-compose.yml": """\
version: "3.8"
services:
  app:
    build: .
    ports:
      - "3000:3000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: extrace_user
      POSTGRES_PASSWORD: Xk9$$mP2vL7nQ
      POSTGRES_DB: extrace_prod
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass r3d1sP@ssExtrace
    ports:
      - "6379:6379"

volumes:
  pgdata:
""",
    "Dockerfile": """\
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY .env .env
EXPOSE 3000
CMD ["gunicorn", "src.app:app", "-b", "0.0.0.0:3000"]
""",
    # --- Config files ---
    "requirements.txt": """\
flask==3.0.0
flask-sqlalchemy==3.1.1
psycopg2-binary==2.9.9
redis==5.0.1
stripe==7.0.0
boto3==1.29.0
PyJWT==2.8.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
""",
    "package.json": """\
{
  "name": "extrace-backend",
  "version": "2.1.0",
  "private": true,
  "scripts": {
    "migrate": "alembic upgrade head",
    "seed": "python scripts/seed.py"
  }
}
""",
    # --- GCP service account ---
    "credentials/gcp-service-account.json": """\
{
  "type": "service_account",
  "project_id": "extrace-prod-123456",
  "private_key_id": "key123456789",
  "private_key": "EXTRACE_FAKE_RSA_KEY\\nthis-is-only-a-honeypot-canary\\nEXTRACE_FAKE_RSA_KEY_END\\n",
  "client_email": "extrace-sa@extrace-prod-123456.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
""",
    # --- Firebase ---
    "credentials/firebase-admin-sdk.json": """\
{
  "type": "service_account",
  "project_id": "extrace-app",
  "private_key_id": "fb-key-extrace-001",
  "private_key": "EXTRACE_FAKE_RSA_KEY\\nthis-is-only-a-honeypot-canary\\nEXTRACE_FAKE_RSA_KEY_END\\n",
  "client_email": "firebase-adminsdk-abc12@extrace-app.iam.gserviceaccount.com",
  "client_id": "109876543210987654321"
}
""",
    # --- Terraform ---
    "infra/terraform.tfvars": """\
db_password       = "Xk9$mP2vL7nQ"
redis_password    = "r3d1sP@ssExtrace"
api_secret_key    = "extrace-jwt-sup3r-s3cret-k3y-2024-pr0duction"
domain            = "extrace.io"
""",
    "infra/main.tf": """\
provider "aws" {
  region = "eu-west-1"
}

resource "aws_db_instance" "production" {
  identifier     = "extrace-prod-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"
  username       = "extrace_user"
  password       = var.db_password
  db_name        = "extrace_prod"
}
""",
    # --- Alembic migration ---
    "alembic/env.py": """\
from alembic import context
from src.database import db
import os

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/extrace"),
)
""",
    # --- Scripts with hardcoded values ---
    "scripts/deploy.sh": """\
#!/bin/bash
set -e

echo "Deploying to production..."
export DATABASE_URL="postgresql://extrace_user:Xk9\\$mP2vL7nQ@db.extrace.io:5432/extrace_prod"
docker login ghcr.io -u extrace -p ghp_R8nFakePatTokenExtrace7890123456
docker build -t ghcr.io/extrace-io/backend:latest .
docker push ghcr.io/extrace-io/backend:latest
ssh deploy@10.0.1.50 "cd /opt/extrace && docker-compose pull && docker-compose up -d"
echo "Deploy complete!"
""",
    "scripts/seed.py": """\
import psycopg2

conn = psycopg2.connect(
    host="db.extrace.io",
    port=5432,
    user="extrace_user",
    password="Xk9$mP2vL7nQ",
    dbname="extrace_prod",
)

cur = conn.cursor()
cur.execute("INSERT INTO users (email, role) VALUES ('admin@extrace.io', 'admin')")
conn.commit()
conn.close()
""",
    "scripts/backup.sh": """\
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump "postgresql://extrace_user:Xk9\\$mP2vL7nQ@db.extrace.io:5432/extrace_prod" \
  | gzip > /tmp/backup_${TIMESTAMP}.sql.gz
aws s3 cp /tmp/backup_${TIMESTAMP}.sql.gz s3://extrace-backups/db/
echo "Backup uploaded: backup_${TIMESTAMP}.sql.gz"
""",
    # --- Crypto wallet (extra bait) ---
    ".wallet/keystore.json": """\
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18",
  "crypto": {
    "cipher": "aes-128-ctr",
    "ciphertext": "fake-ciphertext-extrace-honeypot-0123456789abcdef",
    "kdf": "scrypt"
  },
  "version": 3
}
""",
    # --- README ---
    "README.md": """\
# ExTrace Backend

Production backend for the ExTrace platform.

## Quick Start

```bash
cp .env.local .env
docker-compose up -d
python -m flask run
```

## Deployment

```bash
./scripts/deploy.sh
```
""",
}


def setup_dev_environment() -> None:
    """Create a realistic developer honeypot environment.

    Sets up fake but realistic-looking credentials, config files, and
    source code both in /workspace and /home/executor to attract
    malicious extensions that scan for secrets.
    """
    # --- Workspace files (project directory) ---
    create_workspace_structure(_WORKSPACE_FILES)

    # --- Multi-language sample files (for onLanguage:* activation) ---
    create_workspace_structure(_LANGUAGE_SAMPLE_FILES)

    # --- Workspace pattern files (for workspaceContains:* activation) ---
    create_workspace_structure(_WORKSPACE_PATTERN_FILES)

    # Make scripts executable
    for script in ["scripts/deploy.sh", "scripts/backup.sh", "scripts/migrate.rb"]:
        path = WORKSPACE_DIR / script
        if path.exists():
            path.chmod(path.stat().st_mode | stat.S_IEXEC)

    # --- Home directory files (user profile) ---
    for rel_path, content in _HOME_FILES.items():
        path = HOME_DIR / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    # SSH key permissions (realistic)
    ssh_key = HOME_DIR / ".ssh" / "id_rsa"
    if ssh_key.exists():
        ssh_key.chmod(0o600)
    ssh_dir = HOME_DIR / ".ssh"
    if ssh_dir.exists():
        ssh_dir.chmod(0o700)


if __name__ == "__main__":
    print("[*] Setting up developer environment...")
    setup_dev_environment()
    print("[+] Environment ready: .env, SSH keys, AWS creds, source code, etc.")
