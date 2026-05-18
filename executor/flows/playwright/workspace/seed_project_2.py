"""Project seed data part 2 for the Playwright workspace fixtures."""

WORKSPACE_FILES = {
    "src/storage.py": "import boto3\n"
    "import os\n"
    "\n"
    "s3 = boto3.client(\n"
    '    "s3",\n'
    '    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),\n'
    '    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),\n'
    '    region_name=os.environ.get("AWS_REGION", "eu-west-1"),\n'
    ")\n"
    "\n"
    'BUCKET = os.environ.get("S3_BUCKET", "extrace-uploads-prod")\n'
    "\n"
    "\n"
    "def upload_file(file_path: str, key: str):\n"
    "    s3.upload_file(file_path, BUCKET, key)\n"
    '    return f"https://{BUCKET}.s3.amazonaws.com/{key}"\n',
    "src/utils.py": "import hashlib\n"
    "import secrets\n"
    "\n"
    "\n"
    "def generate_api_key() -> str:\n"
    '    return f"extrace_{secrets.token_hex(32)}"\n'
    "\n"
    "\n"
    'def hash_password(password: str, salt: str = "extrace-salt-2024") -> str:\n'
    '    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()\n',
    "frontend/src/api.js": "const API_BASE = process.env.REACT_APP_API_URL || "
    '"https://api.extrace.io";\n'
    "\n"
    "export async function fetchWithAuth(endpoint, options = {}) {\n"
    '  const token = localStorage.getItem("auth_token");\n'
    "  return fetch(`${API_BASE}${endpoint}`, {\n"
    "    ...options,\n"
    "    headers: {\n"
    "      ...options.headers,\n"
    "      Authorization: `Bearer ${token}`,\n"
    '      "Content-Type": "application/json",\n'
    "    },\n"
    "  });\n"
    "}\n",
    "frontend/.env": "REACT_APP_API_URL=https://api.extrace.io\n"
    "REACT_APP_STRIPE_PK=pk_live_fakeStripePublishableKeyExtrace\n"
    "REACT_APP_SENTRY_DSN=https://fakekey@o123456.ingest.sentry.io/1234567\n",
    "frontend/package.json": "{\n"
    '  "name": "extrace-frontend",\n'
    '  "version": "1.2.0",\n'
    '  "private": true,\n'
    '  "dependencies": {\n'
    '    "react": "^18.2.0",\n'
    '    "react-dom": "^18.2.0",\n'
    '    "@stripe/stripe-js": "^1.54.0",\n'
    '    "axios": "^1.6.0"\n'
    "  },\n"
    '  "scripts": {\n'
    '    "start": "react-scripts start",\n'
    '    "build": "react-scripts build",\n'
    '    "test": "react-scripts test"\n'
    "  }\n"
    "}\n",
    "docker-compose.yml": 'version: "3.8"\n'
    "services:\n"
    "  app:\n"
    "    build: .\n"
    "    ports:\n"
    '      - "3000:3000"\n'
    "    env_file:\n"
    "      - .env\n"
    "    depends_on:\n"
    "      - db\n"
    "      - redis\n"
    "\n"
    "  db:\n"
    "    image: postgres:16-alpine\n"
    "    environment:\n"
    "      POSTGRES_USER: extrace_user\n"
    "      POSTGRES_PASSWORD: Xk9$$mP2vL7nQ\n"
    "      POSTGRES_DB: extrace_prod\n"
    "    ports:\n"
    '      - "5432:5432"\n'
    "    volumes:\n"
    "      - pgdata:/var/lib/postgresql/data\n"
    "\n"
    "  redis:\n"
    "    image: redis:7-alpine\n"
    "    command: redis-server --requirepass r3d1sP@ssExtrace\n"
    "    ports:\n"
    '      - "6379:6379"\n'
    "\n"
    "volumes:\n"
    "  pgdata:\n",
    "Dockerfile": "FROM python:3.11-slim\n"
    "WORKDIR /app\n"
    "COPY requirements.txt .\n"
    "RUN pip install --no-cache-dir -r requirements.txt\n"
    "COPY src/ src/\n"
    "COPY .env .env\n"
    "EXPOSE 3000\n"
    'CMD ["gunicorn", "src.app:app", "-b", "0.0.0.0:3000"]\n',
    "requirements.txt": "flask==3.0.0\n"
    "flask-sqlalchemy==3.1.1\n"
    "psycopg2-binary==2.9.9\n"
    "redis==5.0.1\n"
    "stripe==7.0.0\n"
    "boto3==1.29.0\n"
    "PyJWT==2.8.0\n"
    "gunicorn==21.2.0\n"
    "python-dotenv==1.0.0\n"
    "requests==2.31.0\n",
    "package.json": "{\n"
    '  "name": "extrace-backend",\n'
    '  "version": "2.1.0",\n'
    '  "private": true,\n'
    '  "scripts": {\n'
    '    "migrate": "alembic upgrade head",\n'
    '    "seed": "python scripts/seed.py"\n'
    "  }\n"
    "}\n",
    "credentials/gcp-service-account.json": "{\n"
    '  "type": "service_account",\n'
    '  "project_id": "extrace-prod-123456",\n'
    '  "private_key_id": "key123456789",\n'
    '  "private_key": '
    '"EXTRACE_FAKE_RSA_KEY\\nthis-is-only-a-honeypot-canary\\nEXTRACE_FAKE_RSA_KEY_END\\n",\n'
    '  "client_email": '
    '"extrace-sa@extrace-prod-123456.iam.gserviceaccount.com",\n'
    '  "client_id": "123456789012345678901",\n'
    '  "auth_uri": '
    '"https://accounts.google.com/o/oauth2/auth",\n'
    '  "token_uri": "https://oauth2.googleapis.com/token"\n'
    "}\n",
}
