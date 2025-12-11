# ExTrace - VS Code Extension Security Scanner

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**A security-focused REST API for scanning and cataloging VS Code extensions**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Project Structure](#-project-structure)

</div>

---

## 📋 Overview

ExTrace is a backend API service designed to scan, validate, and store metadata from VS Code extensions. It's built for security researchers and developers who need to analyze extension manifests at scale.

### What It Does

1. **Scans** extension directories for `package.json` files
2. **Validates** manifest data against strict Pydantic schemas
3. **Stores** extension metadata in PostgreSQL for querying
4. **Serves** data via RESTful API endpoints

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Extension Scanning** | Parse and validate VS Code extension manifests |
| 🗄️ **PostgreSQL Storage** | Persistent storage with JSONB support for complex data |
| 📡 **REST API** | FastAPI-powered endpoints with automatic OpenAPI docs |
| 🐳 **Docker Ready** | Multi-service Docker Compose setup |
| 🔒 **Security First** | Non-root containers, input validation, SQL injection prevention |
| 📊 **Optimized Queries** | Indexed fields, partial column loading for performance |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ExTrace Architecture                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │   Client     │────▶│   FastAPI    │────▶│   PostgreSQL DB      │    │
│  │  (Browser)   │◀────│   (Uvicorn)  │◀────│   (Docker)           │    │
│  └──────────────┘     └──────────────┘     └──────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│                       ┌──────────────┐                                  │
│                       │  extensions/ │                                  │
│                       │  (Filesystem)│                                  │
│                       └──────────────┘                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Routers (HTTP Layer)                       │
│                         routers/core.py                                 │
│                    Handles HTTP requests/responses                      │
├─────────────────────────────────────────────────────────────────────────┤
│                              Schemas (Validation)                       │
│                         schemas/schemas.py                              │
│                    Pydantic models for validation                       │
├─────────────────────────────────────────────────────────────────────────┤
│                              Service (Business Logic)                   │
│                         scanner/service.py                              │
│                    Orchestrates operations                              │
├─────────────────────────────────────────────────────────────────────────┤
│                              CRUD (Data Access)                         │
│                         crud/crud.py                                    │
│                    Database operations                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                              Models (ORM)                               │
│                         models/models.py                                │
│                    SQLAlchemy table definitions                         │
├─────────────────────────────────────────────────────────────────────────┤
│                              Database                                   │
│                         PostgreSQL                                      │
│                    Persistent storage                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/extrace.git
cd extrace
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**.env file:**
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/extrace
PROJECT_NAME=ExTrace API
ENV=dev
EXTENSION_DIR=extensions
```

### 3. Start with Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Run Database Migrations

```bash
# Apply migrations
docker-compose exec api alembic upgrade head
```

### 5. Access the API

- **API Root:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📡 API Reference

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `GET` | `/searchExtension?name=...` | Search extension by name |
| `GET` | `/getExtensionsBaseInfo` | List all extensions (minimal) |
| `GET` | `/getExtensionsAllInfo` | List all extensions (full) |
| `POST` | `/createExtension` | Scan and create extension |

### Detailed API

#### Search Extension
```http
GET /searchExtension?name=python
```

**Response:**
```json
{
  "name": "python",
  "publisher": "ms-python",
  "engines": {"vscode": "^1.95.0"},
  "displayName": "Python",
  "description": "Python language support...",
  "categories": ["Programming Languages", "Linters"],
  "icon": "https://..."
}
```

#### Create Extension
```http
POST /createExtension
Content-Type: application/json

{
  "name": "python"
}
```

**Response:** Created extension object

**Status Codes:**
- `200` - Success
- `404` - Extension not found in filesystem
- `409` - Extension already exists (duplicate)

---

## 📁 Project Structure

```
extrace/
├── main.py                 # Application entry point
├── docker-compose.yml      # Multi-service Docker setup
├── alembic.ini             # Alembic configuration
├── .env.example            # Environment template
│
├── core/                   # Core configuration
│   ├── config.py           # Pydantic Settings
│   └── deps.py             # Dependency injection
│
├── database/               # Database configuration
│   └── session.py          # SQLAlchemy engine/session
│
├── models/                 # ORM models
│   └── models.py           # Extension table definition
│
├── schemas/                # Pydantic schemas
│   └── schemas.py          # Request/response models
│
├── crud/                   # Data access layer
│   └── crud.py             # CRUD operations
│
├── routers/                # API routes
│   ├── core.py             # Main endpoints
│   ├── Dockerfile          # API container
│   └── requirements.txt    # Python dependencies
│
├── scanner/                # Extension scanning
│   ├── service.py          # Business logic
│   └── json_parser.py      # Filesystem operations
│
├── scripts/                # Utility scripts
│   └── seed_test.py        # Database seeding
│
├── alembic/                # Database migrations
│   ├── env.py              # Migration configuration
│   └── versions/           # Migration files
│
└── extensions/             # VS Code extensions directory
    └── publisher.ext-1.0/  # Extracted extensions
        └── package.json
```

---

## 🗄️ Database Schema

### Extensions Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `name` | VARCHAR | Extension identifier (indexed) |
| `publisher` | VARCHAR | Publisher name (indexed) |
| `engines` | JSONB | VS Code version requirements |
| `license` | VARCHAR | SPDX license |
| `displayName` | VARCHAR | Human-readable name |
| `description` | TEXT | Extension description |
| `categories` | ARRAY | Marketplace categories |
| `keywords` | ARRAY | Search keywords |
| `galleryBanner` | JSONB | Banner styling |
| `preview` | BOOLEAN | Preview flag |
| `badges` | JSONB | Status badges |
| `markdown` | TEXT | Markdown preference |
| `qna` | JSONB | Q&A configuration |
| `sponsor` | JSONB | Sponsor info |
| `icon` | VARCHAR | Icon URL |
| `pricing` | VARCHAR | Pricing tier |
| `main` | VARCHAR | Desktop entry point |
| `web` | VARCHAR | Web entry point |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

**Constraints:**
- Unique: (`publisher`, `name`)
- Indexes: `name`, `publisher`

---

## 🔧 Development

### Local Setup (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r routers/requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

### Seed Test Data

```bash
python scripts/seed_test.py
```

---

## 🔒 Security Features

| Feature | Implementation |
|---------|---------------|
| **Input Validation** | Pydantic schemas with type checking |
| **SQL Injection Prevention** | SQLAlchemy ORM with parameterized queries |
| **Non-root Container** | Docker runs as `appuser` |
| **Unique Constraints** | Prevents duplicate entries |
| **Error Handling** | Structured error responses |

---

## 📊 Performance Optimizations

- **Indexed Columns**: `name` and `publisher` for fast lookups
- **Partial Loading**: `load_only()` for lightweight queries
- **Connection Pooling**: SQLAlchemy manages connection reuse
- **JSONB Storage**: Efficient querying of nested data

---

## 🗺️ Roadmap

### Current Sprint: Database Foundation ✅
- [x] PostgreSQL + Docker setup
- [x] SQLAlchemy models
- [x] Alembic migrations
- [x] Basic CRUD operations
- [x] Pydantic v2 schemas
- [x] FastAPI router structure

### Next Sprint: Scanner Core
- [ ] Detailed manifest parsing
- [ ] Dangerous pattern detection
- [ ] Permission analysis
- [ ] Risk scoring

### Future Sprints
- [ ] Structured logging
- [ ] Test infrastructure
- [ ] CLI interface
- [ ] Web dashboard

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Pydantic](https://docs.pydantic.dev/) - Data validation library
- [VS Code Extension API](https://code.visualstudio.com/api) - Extension manifest reference

---

<div align="center">
  <strong>Built with ❤️ for extension security</strong>
</div>
