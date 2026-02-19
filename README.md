# 🔮 ExTrace - VS Code Extension Security

<div align="center">

<br>

**A Secure VS Code Extension Analysis Platform**

<br>

[![Python](https://img.shields.io/badge/Python-3.11-9b59b6?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00d4aa?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-3498db?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-e74c3c?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-f1c40f?style=for-the-badge&logo=open-source-initiative&logoColor=white)](LICENSE)

<br>

---

`Last Updated: 2026-02-19` • `Version: 1.0.0` • `Status: Active`

---

</div>

<br>

## 📑 Table of Contents

<details>
<summary><strong>🗂️ Click to expand navigation</strong></summary>

<br>

| Section | Description |
|:--------|:------------|
| [📋 Overview](#-overview) | Project goals and functionality |
| [✨ Features](#-features) | Key capabilities and tech highlights |
| [🏗️ Architecture](#️-architecture) | System design and component diagrams |
| [🚀 Quick Start](#-quick-start) | Setup and installation guide |
| [📡 API Reference](#-api-reference) | Endpoint documentation and examples |
| [📁 Project Structure](#-project-structure) | File layout and organization |
| [🗄️ Database Schema](#️-database-schema) | Data models and storage |
| [🔧 Development](#-development) | Local dev and testing capability |

</details>

<br>

---

<br>

## 📋 Overview

> [!CAUTION]
> **Internal Use Only**: ExTrace is designed for isolated security research environments. It does not include built-in authentication or rate-limiting, assuming it runs within a trusted, firewalled network or a local containerized environment.

ExTrace is a security analysis platform with a FastAPI backend and a Streamlit dashboard for activation intelligence. It is designed to **scan**, **validate**, and **store** VS Code extension metadata, then visualize dynamic activation behavior for research workflows.

<br>

### 🎯 Core Capabilities

1.  **🔍 Scan**: Recursively scans extension directories for `package.json` files.
2.  **✅ Validate**: Enforces strict Pydantic schemas on manifest data.
3.  **💾 Store**: Persists extension metadata in PostgreSQL with JSONB support.
4.  **📡 Serve**: Provides a high-performance RESTful API for querying data.
5.  **🖥️ Visualize**: Provides an activation intelligence dashboard backed by `/api/activations`.

<br>

---

<br>

## ✨ Features

<br>

| Feature | Description |
|:--------|:------------|
| 🔍 **Extension Scanning** | Parse and validate VS Code extension manifests (including capabilities) |
| 🗄️ **PostgreSQL Storage** | Persistent storage with JSONB support for complex data |
| 📡 **REST API** | FastAPI-powered endpoints with automatic OpenAPI docs |
| 🐳 **Docker Ready** | Multi-service Docker Compose setup |
| 🔒 **Security First** | Non-root containers, input validation, SQL injection prevention |
| 📊 **Optimized Queries** | Indexed fields, partial column loading for performance |
| 🤖 **Automation-Ready** | Foundations for dynamic analysis and interaction workflows |
| 🖥️ **Intelligence Dashboard** | Streamlit UI for activation timelines, latency analysis, and raw report inspection |

<br>

---

<br>

## 🏗️ Architecture

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#7c3aed', 'primaryTextColor': '#e6edf3', 'lineColor': '#22d3ee', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart LR
    subgraph ClientLayer["👤 CLIENT LAYER"]
        Client[("Browser / API Client")]
    end

    subgraph ServiceLayer["☁️ SERVICE LAYER"]
        FastAPI["⚡ FastAPI (Uvicorn)"]
    end

    subgraph DataLayer["🗄️ DATA LAYER"]
        PG[("🐘 PostgreSQL")]
        FS[("📁 extensions/")]
    end

    ClientLayer <-->|"HTTP/REST"| ServiceLayer
    ServiceLayer <-->|"SQL (SQLAlchemy)"| PG
    ServiceLayer -->|"File I/O"| FS

    style ClientLayer fill:#7c3aed,stroke:#a855f7,stroke-width:3px,color:#fff
    style ServiceLayer fill:#0891b2,stroke:#22d3ee,stroke-width:3px,color:#fff
    style DataLayer fill:#059669,stroke:#34d399,stroke-width:3px,color:#fff
```

<br>

### 📚 Layered Design

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#be185d', 'primaryTextColor': '#e6edf3', 'lineColor': '#f472b6', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TD
    Router["🌐 Routers (HTTP)"]
    Schema["📝 Schemas (Validation)"]
    Service["⚙️ Service (Logic)"]
    CRUD["💾 CRUD (DB Access)"]
    Model["📋 Models (ORM)"]
    DB[("🐘 Database")]

    Router --> Schema
    Router --> Service
    Service --> CRUD
    CRUD --> Model
    Model --> DB

    style Router fill:#be185d,stroke:#ec4899,stroke-width:2px,color:#fff
    style Schema fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff
    style Service fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff
    style CRUD fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
    style Model fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#fff
    style DB fill:#1d4ed8,stroke:#60a5fa,stroke-width:2px,color:#fff
```

<br>

---

<br>

## 🚀 Quick Start

<br>

### Prerequisites

- 🐳 Docker & Docker Compose
- 🐍 Python 3.11+ (for local development)
- 🐙 Git

<br>

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/extrace.git
cd extrace
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env
```

> [!TIP]
> Edit `.env` to match your local configuration if needed.

**Default `.env` (recommended for local dev):**
```env
# Database (used for local dev / docker-compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=extrace

# Optional override (Docker/CI)
# DATABASE_URL=postgresql://postgres:postgres@postgres:5432/extrace

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_DEBUG=true

# Project
PROJECT_NAME="ExTrace API"
PROJECT_ENV=dev
PROJECT_VERSION=1.0.0
PROJECT_EXTENSION_DIR=extensions
```

> [!NOTE]
> `DATABASE_URL` (if set) overrides `POSTGRES_*` values. See `.env.example` for the full template.

### 3. Start with Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Run Database Migrations

```bash
# Apply migrations inside the container
docker-compose exec api alembic upgrade head
```

### 5. Access Services

- **🌐 API Root:** `http://localhost:8000`
- **📄 Swagger UI:** `http://localhost:8000/docs`
- **📚 ReDoc:** `http://localhost:8000/redoc`
- **🖥️ Streamlit Dashboard:** `http://localhost:3000`
- **🌐 noVNC (Executor GUI):** `http://localhost:6080/vnc.html`

### 6. Generate Activation Reports (Optional)

```bash
# Run executor automation and generate activation report JSON in output/
make exec-run

# Start only the Streamlit UI service (if needed)
make ui-up
```

<br>

---

<br>

## 📡 API Reference

<br>

### Endpoints Overview

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `GET` | `/searchExtension` | Search by `name`, `publisher`, `version` |
| `GET` | `/getExtensionsBaseInfo` | List all extensions (minimal) |
| `GET` | `/getExtensionsAllInfo` | List all extensions (full) |
| `POST` | `/createExtension` | Scan and create extension |
| `DELETE` | `/deleteExtension` | Delete by `name`, `publisher`, `version` |
| `GET` | `/getExtensionScripts` | List extension npm scripts |
| `GET` | `/getExtensionActivationEvents` | List activation events |
| `GET` | `/getExtensionCapabilities` | Get capability declarations |
| `GET` | `/getExtensionContributesAll` | Get contributes container |
| `GET` | `/getExtensionContributesCommands` | Get contributes commands |
| `GET` | `/api/activations` | List activation report files (newest first) |
| `GET` | `/api/activations/latest` | Get the most recent activation report |
| `GET` | `/api/activations/{name}` | Get a specific activation report by filename |

<br>

**Query Parameters**

| Endpoint | Parameters |
|:---------|:-----------|
| `/searchExtension` | `name` (required), `publisher` (optional), `version` (optional) |
| `/deleteExtension` | `name` (required), `publisher` (optional), `version` (optional) |
| `/getExtensionScripts` | `name` (required), `publisher` (optional), `version` (optional) |
| `/getExtensionActivationEvents` | `name` (required), `publisher` (optional), `version` (optional) |
| `/getExtensionCapabilities` | `name` (required), `publisher` (optional), `version` (optional) |
| `/getExtensionContributesAll` | `name` (required), `publisher` (optional), `version` (optional) |
| `/getExtensionContributesCommands` | `name` (required), `publisher` (optional), `version` (optional) |
| `/getExtensionsAllInfo` | `skip` (optional), `limit` (optional) |
| `/api/activations/{name}` | `name` (required path parameter, filename only) |

<br>

### 📝 Example Usage

#### Search Extension
```http
GET /searchExtension?name=python
```

<details>
<summary><strong>See Response</strong></summary>

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
</details>

#### Create Extension
```http
POST /createExtension
Content-Type: application/json

{
  "name": "python"
}
```

#### Delete Extension
```http
DELETE /deleteExtension?name=python
```

> [!TIP]
> All search/delete endpoints require `name`. For unambiguous results, also pass
> `publisher` and `version` because the unique constraint is `(publisher, name, version)`.

> [!IMPORTANT]
> `/createExtension` performs an exact match on the `package.json` `"name"` field
> under `PROJECT_EXTENSION_DIR`. The folder name is not used for matching.

> [!NOTE]
> `/api/activations/{name}` rejects traversal patterns (`..`, `/`, `\`) and returns `400` for invalid filenames.

### 📊 Activation Dashboard Data Source

- The UI reads report metadata from `GET /api/activations`.
- The "latest session" view reads from `GET /api/activations/latest`.
- Session-specific view reads from `GET /api/activations/{name}`.
- Latest and named report responses include `_metadata.filename`.

<br>

---

<br>

## 📁 Project Structure

<br>

```
extrace/
├── documents/              # 📚 Architecture, testing, reviews
├── main.py                 # 🚀 Application entry point
├── docker-compose.yml      # 🐳 Multi-service Docker setup
├── alembic.ini             # 🔄 Alembic configuration
├── Makefile                # 🧰 Dev / test / lint commands
├── .env.example            # 🔐 Environment template
│
├── core/                   # ⚡ Core configuration
│   ├── config.py           # Pydantic Settings
│   └── deps.py             # Dependency injection
│
├── database/               # 🔌 Database layer
│   └── session.py          # SQLAlchemy engine/session
│
├── models/                 # 📋 ORM models
│   └── models.py           # Extension table definition
│
├── schemas/                # 📝 Pydantic schemas
│   └── schemas.py          # Request/response models
│
├── crud/                   # 💾 Data access layer
│   └── crud.py             # CRUD operations
│
├── routers/                # 🌐 API routes
│   ├── core.py             # Main endpoints
│   ├── activations.py      # Activation reports endpoints
│   ├── Dockerfile          # API container
│   └── requirements.txt    # Python dependencies
│
├── scanner/                # ⚙️ Business logic
│   ├── service.py          # Business logic
│   └── json_parser.py      # Filesystem operations
│
├── executor/               # 🎭 Dynamic analysis runtime (Docker + Xvfb)
│   ├── Dockerfile          # Executor container image
│   └── start.sh            # Xvfb/openbox/x11vnc/noVNC startup
│
├── ui/                     # 🖥️ Streamlit intelligence dashboard
│   ├── app.py              # Dashboard application
│   ├── Dockerfile          # UI container
│   └── .streamlit/config.toml
│
├── scripts/                # 🛠️ Utility scripts
│   └── seed_test.py        # Database seeding
│
├── alembic/                # 🔄 Database migrations
│   ├── env.py              # Migration configuration
│   └── versions/           # Migration files
│
├── output/                 # 📄 Activation report JSON artifacts
├── extensions/             # 📦 VS Code extensions directory
│   └── ...
└── tests/                  # 🧪 Pytest suite
```

<br>

---

<br>

## 🗄️ Database Schema

<br>

### Extensions Table

| Column | Type | Description |
|:-------|:-----|:------------|
| `id` | `SERIAL` | **PK**: Primary key |
| `name` | `VARCHAR` | **Indexed** |
| `version` | `VARCHAR` | **Indexed** |
| `publisher` | `VARCHAR` | **Indexed** |
| `engines` | `JSONB` | VS Code requirements |
| `license` | `VARCHAR` | SPDX license |
| `displayName` | `VARCHAR` | Human-readable name |
| `keywords` | `ARRAY` | Search keywords |
| `categories` | `ARRAY` | Marketplace categories |
| `dependencies` | `JSONB` | Runtime dependencies |
| `devDependencies` | `JSONB` | Dev dependencies |
| `extensionPack` | `ARRAY` | Bundled extension IDs |
| `extensionDependencies` | `ARRAY` | Dependent extension IDs |
| `extensionKind` | `ARRAY` | UI/Workspace kind |
| `npm_fields` | `JSONB` | Standard npm fields (repo, author, etc.) |
| `extra_fields` | `JSONB` | Unknown/Custom fields from package.json |

> [!IMPORTANT]
> A **Unique Constraint** applies to `(publisher, name, version)` to prevent duplicate entries.

<br>

### Related Tables

| Table | Relationship | Description |
|:------|:-------------|:------------|
| `extension_capabilities` | 1:1 | Workspace trust & virtual workspace settings |
| `extension_scripts` | 1:N | npm scripts from package.json |
| `extension_activation_events` | 1:N | Activation events (onLanguage, onCommand, etc.) |
| `extension_contributes` | 1:1 | Parent table for contribution points |
| `extension_contributes_commands` | 1:N | Commands from contributes.commands |
| `extension_contributes_keybindings` | 1:N | Keybindings from contributes.keybindings |
| `extension_contributes_menus` | 1:N | Menu items from contributes.menus |
| `extension_contributes_authentication`| 1:N | Auth providers from contributes.authentication|
| `extension_contributes_terminal` | 1:N | Terminal profiles from contributes.terminal |

<br>

---

<br>

## 🔧 Development

<br>

### Local Setup (No Docker)

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

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

> 📘 For detailed testing guidelines, see [TESTING.md](documents/TESTING.md).
> For local DB-backed tests, you can also run `make test-local` which boots `postgres_test`.

<br>

---

<br>

## 🧰 Common Commands

```bash
# Format + lint + typecheck + test
make check-all

# Start docker services
make up

# Stop docker services
make down

# Run dynamic analysis and generate activation report
make exec-run

# Start dashboard service
make ui-up

# Run migrations
make migrate
```

<br>

---

<br>

## ⚙️ Configuration

Key environment variables (see `.env.example` for the full list):

| Prefix | Variables | Purpose |
|:------:|:----------|:--------|
| `POSTGRES_` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_TEST_PORT` | Database connectivity (dev + test) |
| `API_` | `API_HOST`, `API_PORT`, `API_WORKERS`, `API_DEBUG` | API server configuration |
| `EXECUTOR_` | `EXECUTOR_DISPLAY`, `EXECUTOR_NOVNC_PORT`, `EXECUTOR_OUTPUT_HOST_PATH` | Executor runtime and output/report paths |
| `PROJECT_` | `PROJECT_NAME`, `PROJECT_ENV`, `PROJECT_VERSION`, `PROJECT_EXTENSION_DIR` | Project metadata and scan directory |
| `UI_` | `UI_PORT` | Streamlit dashboard service port |
| (optional) | `DATABASE_URL` | Overrides `POSTGRES_*` when set (Docker/CI) |

<br>

## 📚 Additional Docs

- [Architecture Overview](documents/ARCHITECTURE.md)
- [Testing Guide](documents/TESTING.md)
- [Development Priorities](documents/DEVELOPMENT_PRIORITIES.md)
- [Architecture Audit](documents/ARCHITECTURE_AUDIT.md)
- [Dynamic Analysis TODO](documents/automation_todo.md)
- [Executor Playwright Guide](documents/EXECUTOR_PLAYWRIGHT.md)

<br>

---

<br>

## 🗺️ Roadmap

### ✅ Phase 0: Metadata Parsing (Completed)
- [x] PostgreSQL + Docker Setup
- [x] SQLAlchemy 2.0 Models & Alembic Migrations
- [x] CRUD Operations
- [x] Extension metadata parsing (`package.json`)
- [x] Activation events, capabilities, contributes extraction
- [x] REST API endpoints

### 🚧 Phase 1: Xvfb Dynamic Analysis (In Progress)
> **Full GUI execution via Xvfb** | Current automated coverage: 12/25 activation events (~48%)

- [x] Docker executor image (Ubuntu 22.04 + Xvfb + VS Code)
- [x] Playwright UI automation helpers (CDP-based)
- [x] Honeypot developer environment (fake credentials, secrets)
- [x] VS Code auto-configuration (trust/telemetry disabled)
- [x] noVNC browser access for debugging
- [x] 10 user behavior simulation scenarios (all passing)
- [x] Extension Host activation monitoring (log parsing + UI scraping)
- [x] Multi-language sample files for activation coverage (20+ languages)
- [x] Preliminary capture of network (`.pcap`) and filesystem (`inotify`) events
- [ ] Automated extension install/uninstall lifecycle
- [ ] Production-ready Network monitoring (tshark integration)
- [ ] Production-ready Process monitoring (strace integration)
- [ ] Analysis results database schema & persistence
- [ ] Risk scoring engine logic
- [ ] Analysis API endpoints (`/analyze`)

### 🔮 Phase 2: Persona Simulation & Advanced Analysis (Future)
> **Prerequisite:** Phase 1 complete

- [ ] Persona-based simulation (Curious, Cautious, Impatient, Normal)
- [ ] Screenshot/screen recording capture
- [ ] Anti-fingerprinting measures
- [ ] Behavioral realism (human-like interactions)
- [ ] WebView interaction

### 📊 Phase 3: Reporting & Visualization (Started)
- [x] Activation Intelligence Dashboard (Streamlit)
- [ ] Risk report generation
- [ ] Domain relationship graphs
- [ ] Action → consequence timeline

> **See:** [Dynamic Analysis TODO](documents/automation_todo.md) for detailed tasks

<br>

---

<div align="center">

**Built with ❤️ for extension security**

</div>
