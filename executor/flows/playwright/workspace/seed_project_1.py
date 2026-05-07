"""Project seed data part 1 for the Playwright workspace fixtures."""

WORKSPACE_FILES = {
    ".env": "# App Configuration\n"
    "NODE_ENV=production\n"
    "PORT=3000\n"
    "\n"
    "# Database\n"
    "DATABASE_URL=postgresql://extrace_user:Xk9$mP2vL7nQ@db.extrace.io:5432/extrace_prod\n"
    "REDIS_URL=redis://:r3d1sP@ssExtrace@cache.extrace.io:6379/0\n"
    "\n"
    "# Auth & API Keys\n"
    "JWT_SECRET=extrace-jwt-sup3r-s3cret-k3y-2024-pr0duction\n"
    "SESSION_SECRET=s3ss10n-k3y-extrace-d0nt-share\n"
    "\n"
    "# Third-party Services\n"
    "OPENAI_API_KEY=sk-proj-fakeOpenAIKeyForExtraceHoneypot1234567890abcdef\n"
    "STRIPE_SECRET_KEY=sk_live_fakeStripeKeyExtrace567890\n"
    "STRIPE_WEBHOOK_SECRET=whsec_fakeStripeWebhookExtrace123\n"
    "SENDGRID_API_KEY=SG.fakeExtraceSendGridKey.abcdefghijklmnopqrstuvwxyz012345\n"
    "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX\n"
    "SENTRY_DSN=https://fakekey@o123456.ingest.sentry.io/1234567\n"
    "\n"
    "# AWS (duplicated for app use)\n"
    "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXTRACE\n"
    "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXTRACEKEY\n"
    "AWS_REGION=eu-west-1\n"
    "S3_BUCKET=extrace-uploads-prod\n",
    ".env.production": "DATABASE_URL=postgresql://extrace_prod:Pr0dP@ss!2024@rds.extrace.io:5432/extrace\n"
    "REDIS_URL=redis://prod-cache.extrace.io:6379/0\n"
    "API_KEY=extrace-prod-api-key-7f8a9b0c1d2e\n",
    ".env.local": "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/extrace_dev\n"
    "REDIS_URL=redis://localhost:6379/0\n"
    "DEBUG=true\n"
    "OPENAI_API_KEY=sk-proj-devTestKeyNotReal1234567890\n",
    ".git/config": "[core]\n"
    "    repositoryformatversion = 0\n"
    "    filemode = true\n"
    "    bare = false\n"
    '[remote "origin"]\n'
    "    url = git@github.com:extrace-io/extrace-backend.git\n"
    "    fetch = +refs/heads/*:refs/remotes/origin/*\n"
    '[branch "main"]\n'
    "    remote = origin\n"
    "    merge = refs/heads/main\n",
    ".git/HEAD": "ref: refs/heads/main\n",
    "src/app.py": "from flask import Flask, jsonify\n"
    "from src.config import Config\n"
    "from src.database import db\n"
    "\n"
    "app = Flask(__name__)\n"
    "app.config.from_object(Config)\n"
    "db.init_app(app)\n"
    "\n"
    "\n"
    '@app.route("/api/health")\n'
    "def health():\n"
    '    return jsonify({"status": "ok"})\n'
    "\n"
    "\n"
    '@app.route("/api/users")\n'
    "def get_users():\n"
    '    users = db.session.execute("SELECT * FROM users").fetchall()\n'
    "    return jsonify([dict(u) for u in users])\n"
    "\n"
    "\n"
    'if __name__ == "__main__":\n'
    '    app.run(host="0.0.0.0", port=3000, debug=True)\n',
    "src/config.py": "import os\n"
    "\n"
    "\n"
    "class Config:\n"
    '    SECRET_KEY = os.environ.get("JWT_SECRET", "dev-fallback-secret")\n'
    "    SQLALCHEMY_DATABASE_URI = os.environ.get(\n"
    '        "DATABASE_URL",\n'
    '        "postgresql://postgres:postgres@localhost:5432/extrace_dev",\n'
    "    )\n"
    '    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")\n'
    '    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")\n'
    '    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")\n'
    '    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")\n'
    '    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")\n',
    "src/database.py": "from flask_sqlalchemy import SQLAlchemy\n"
    "\n"
    "db = SQLAlchemy()\n"
    "\n"
    "\n"
    "def get_connection_string():\n"
    "    return "
    '"postgresql://extrace_user:Xk9$mP2vL7nQ@db.extrace.io:5432/extrace_prod"\n',
    "src/auth.py": "import jwt\n"
    "import os\n"
    "\n"
    'JWT_SECRET = os.environ.get("JWT_SECRET", '
    '"extrace-jwt-sup3r-s3cret-k3y-2024-pr0duction")\n'
    'ALGORITHM = "HS256"\n'
    "\n"
    "\n"
    "def create_token(user_id: int) -> str:\n"
    '    payload = {"sub": user_id, "iss": "extrace"}\n'
    "    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)\n"
    "\n"
    "\n"
    "def verify_token(token: str) -> dict:\n"
    "    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])\n",
    "src/payments.py": "import stripe\n"
    "import os\n"
    "\n"
    "stripe.api_key = os.environ.get(\n"
    '    "STRIPE_SECRET_KEY", "sk_live_fakeStripeKeyExtrace567890"\n'
    ")\n"
    "\n"
    "\n"
    "def create_checkout_session(price_id: str, customer_email: str):\n"
    "    return stripe.checkout.Session.create(\n"
    '        payment_method_types=["card"],\n'
    '        line_items=[{"price": price_id, "quantity": 1}],\n'
    '        mode="subscription",\n'
    "        customer_email=customer_email,\n"
    '        success_url="https://extrace.io/success",\n'
    '        cancel_url="https://extrace.io/cancel",\n'
    "    )\n",
}
