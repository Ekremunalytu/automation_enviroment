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

`Last Updated: 2025-12-18` • `Version: 1.1.0` • `Status: Active`

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

> [!NOTE]
> ExTrace is a backend API service designed to **scan**, **validate**, and **store** metadata from VS Code extensions. It's built for security researchers and developers who need to analyze extension manifests at scale.

<br>

### 🎯 Core Capabilities

1.  **🔍 Scan**: Recursively scans extension directories for `package.json` files.
2.  **✅ Validate**: Enforces strict Pydantic schemas on manifest data.
3.  **💾 Store**: Persists extension metadata in PostgreSQL with JSONB support.
4.  **📡 Serve**: Provides a high-performance RESTful API for querying data.

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
| 🛡️ **Trust Analysis** | Parses `untrustedWorkspaces` and `virtualWorkspaces` capabilities |

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

**Default `.env`:**
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
```

### 4. Run Database Migrations

```bash
# Apply migrations inside the container
docker-compose exec api alembic upgrade head
```

### 5. Access the API

- **🌐 API Root:** `http://localhost:8000`
- **📄 Swagger UI:** `http://localhost:8000/docs`
- **📚 ReDoc:** `http://localhost:8000/redoc`

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

<br>

---

<br>

## 📁 Project Structure

<br>

```
extrace/
├── main.py                 # 🚀 Application entry point
├── docker-compose.yml      # 🐳 Multi-service Docker setup
├── alembic.ini             # 🔄 Alembic configuration
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
│   ├── Dockerfile          # API container
│   └── requirements.txt    # Python dependencies
│
├── scanner/                # ⚙️ Business logic
│   ├── service.py          # Business logic
│   └── json_parser.py      # Filesystem operations
│
├── scripts/                # 🛠️ Utility scripts
│   └── seed_test.py        # Database seeding
│
├── alembic/                # 🔄 Database migrations
│   ├── env.py              # Migration configuration
│   └── versions/           # Migration files
│
└── extensions/             # 📦 VS Code extensions directory
    └── ...
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

> [!IMPORTANT]
> A **Unique Constraint** applies to `(publisher, name, version)` to prevent duplicate entries.

<br>

### Related Tables

| Table | Relationship | Description |
|:------|:-------------|:------------|
| `extension_capabilities` | 1:1 | Workspace trust & virtual workspace settings |
| `extension_scripts` | 1:N | npm scripts from package.json |

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

> 📘 For detailed testing guidelines, see [TESTING.md](TESTING.md).

<br>

---

<br>

## 🗺️ Roadmap

### ✅ Completed
- [x] PostgreSQL + Docker Setup
- [x] SQLAlchemy 2.0 Models & Alembic Migrations
- [x] CRUD Operations
- [x] **Capabilities Parsing** (Workspace Trust & Virtual Workspaces)
- [x] **Scripts Parsing** (npm scripts from package.json)

### 🚧 In Progress
- [ ] Detailed manifest parsing (Commands, Events)
- [ ] Risk scoring engine
- [ ] Permission analysis

### 🔮 Future
- [ ] Web Dashboard
- [ ] CLI Interface
- [ ] Structured Logging

<br>

---

<div align="center">

**Built with ❤️ for extension security**

</div>
