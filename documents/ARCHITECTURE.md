<div align="center">

# 🔮 ExTrace Architecture

<br>

**A Secure VS Code Extension Analysis Platform**

<br>

[![Python](https://img.shields.io/badge/Python-3.11-9b59b6?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00d4aa?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-3498db?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-e74c3c?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

<br>

---

`Last Updated: 2026-02-19` • `Version: 1.0.0` • `Status: Development`

---

</div>

<br>

## 📑 Table of Contents

<details>
<summary><strong>🗂️ Click to expand navigation</strong></summary>

<br>

| Section | Description |
|:--------|:------------|
| [🌐 System Overview](#-system-overview) | High-level system components and connections |
| [🏛️ High-Level Architecture](#️-high-level-architecture) | Layer-based architecture overview |
| [📊 Layered Architecture](#-layered-architecture) | Detailed layer breakdown |
| [🔗 Module Dependencies](#-module-dependencies) | Inter-module relationships |
| [🔄 Request Flow](#-request-flow) | API request lifecycle diagrams |
| [🗃️ Database Schema](#️-database-schema) | Data model and constraints |
| [🐳 Docker Infrastructure](#-docker-infrastructure) | Container setup and networking |
| [⚙️ Configuration Flow](#️-configuration-flow) | Settings management |
| [📁 File Structure](#-file-structure) | Project directory layout |
| [📜 Architectural Rules](#-architectural-rules) | Design principles and constraints |
| [🎭 Executor: Playwright UI Automation](#-executor-playwright-ui-automation) | Dynamic analysis automation & honeypot |
| [🔮 Future Architecture](#-future-architecture) | Planned enhancements |
| [📋 Quick Reference](#-quick-reference) | Endpoints and tech stack summary |

</details>

<br>

---

<br>

## 🌐 System Overview

> [!NOTE]
> The system operates within a **Docker-based environment** with isolated containers for the API and database, ensuring security and reproducibility.

<br>

```mermaid
graph TB
    subgraph External
        Client["Client - Browser/API Consumer"]
    end

    subgraph Docker_Environment
        subgraph API_Container
            FastAPI["FastAPI - Uvicorn ASGI"]
        end

        subgraph DB_Container
            PostgreSQL["PostgreSQL - v16 Alpine"]
        end

        subgraph Executor_Container
            VSCode["VS Code + Xvfb - noVNC 6080"]
        end
    end

    subgraph Persistent_Storage
        Extensions["extensions - VS Code Packages"]
        Volumes["postgres_data - Docker Volume"]
        Output["output - Analysis Results"]
    end

    Client -->|HTTP 8000| FastAPI
    Client -->|VNC 6080| VSCode
    FastAPI -->|SQL 5432| PostgreSQL
    FastAPI -->|Read| Extensions
    VSCode -->|Read| Extensions
    VSCode -->|Write| Output
    PostgreSQL -->|Persist| Volumes
```

<br>

---

<br>

## 🎯 Design Philosophy & Constraints

> [!IMPORTANT]
> The architectural decisions in ExTrace are driven by specific operational requirements. Understanding these constraints is crucial for maintaining the "robustness" of the system.

### 1. Robustness over Scalability

**Decision:** The system prioritizes data integrity, type safety, and transactional consistency over high-concurrency throughput.
**Reasoning:** As a security analysis tool, partial or corrupted data is unacceptable. We use strict foreign keys, complex Pydantic validation, and synchronous processing to ensure every scanned extension is recorded perfectly.

### 2. Internal Security Tooling

**Decision:** No built-in authentication or role-based access control (RBAC).
**Reasoning:** ExTrace is designed to run in an isolated, secure environment (e.g., local Docker, air-gapped network) accessible only by security engineers. Security is enforced at the network/infrastructure level rather than the application level.

<br>

---

<br>

## 📡 Telemetry Data Flow (Planned)

> [!NOTE]
> While raw telemetry is captured to the `output/` directory, the following flow describes the planned integration for automated analysis.

```mermaid
flowchart LR
    subgraph ExecutorContainer["🔬 EXECUTOR"]
        VSC["VS Code"] -->|"Net"| TD["tcpdump"]
        VSC -->|"FS"| IN["inotifywait"]
        VSC -->|"Proc"| ST["strace"]
    end

    subgraph APIContainer["⚡ API"]
        LogP["Log Processors"]
    end

    subgraph DB["🐘 DB"]
        Events[("Analysis Events")]
    end

    TD -->|".pcap"| LogP
    IN -->|".log"| LogP
    ST -->|".log"| LogP
    LogP -->|"Insert"| Events
```

1. **Capture:** Raw events are streamed to the `/results` volume.
2. **Ingest:** The API service monitors the output directory for completed analysis runs.
3. **Process:** Log processors parse raw output (PCAP, text) into structured behavioral events.
4. **Store:** Events are persisted in PostgreSQL, linked to the `analysis_runs` table.

### 3. Targeted Single-Scan Workflow

**Decision:** Filesystem scanning is linear and synchronous.
**Reasoning:** The intended workflow is to analyze specific, high-risk extensions one by one or in small batches. The classic "O(N) scanning problem" is mitigated by the operational usage pattern (targeted audits vs. bulk ingestion).

### 4. Xvfb-First Dynamic Analysis

**Decision:** Use Xvfb (virtual display) for all dynamic analysis — full GUI execution only.
**Reasoning:** VS Code extensions require a running Extension Host process to activate, which needs a full GUI instance. Xvfb provides this with low overhead and a single stack for broad activation-event testing. The current Playwright baseline focuses on common/high-value events and is extended incrementally.

<br>

---

<br>

## 🏛️ High-Level Architecture

> [!IMPORTANT]
> ExTrace follows a **strict layered architecture** ensuring separation of concerns and maintainability.

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#a855f7', 'primaryTextColor': '#e6edf3', 'lineColor': '#22d3ee', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart LR
    subgraph Presentation["📡 PRESENTATION LAYER"]
        R[("🌐 Router<br/><small>HTTP Interface</small>")]
    end

    subgraph Business["🧠 BUSINESS LAYER"]
        S[("⚙️ Service<br/><small>Business Logic</small>")]
    end

    subgraph Data["💾 DATA LAYER"]
        C[("📊 CRUD<br/><small>Data Access</small>")]
        P[("📄 Parser<br/><small>File I/O</small>")]
    end

    subgraph Infrastructure["🏗️ INFRASTRUCTURE"]
        M[("📋 Model<br/><small>ORM</small>")]
        DB[("🐘 PostgreSQL")]
        FS[("📁 Filesystem")]
    end

    R -->|"Request"| S
    S -->|"DB Ops"| C
    S -->|"File Ops"| P
    C --> M
    M --> DB
    P --> FS

    S -->|"Response"| R

    style Presentation fill:#7c3aed,stroke:#a855f7,stroke-width:3px,color:#fff
    style Business fill:#be185d,stroke:#ec4899,stroke-width:3px,color:#fff
    style Data fill:#0891b2,stroke:#22d3ee,stroke-width:3px,color:#fff
    style Infrastructure fill:#059669,stroke:#34d399,stroke-width:3px,color:#fff
```

<br>

---

<br>

## 📊 Layered Architecture

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#8b5cf6', 'primaryTextColor': '#e6edf3', 'lineColor': '#f472b6', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TB
    subgraph Layer1["⬆️ LAYER 1: HTTP / API"]
        direction LR
        main["📄 main.py<br/><small>App Factory</small>"]
        router["🔀 routers/core.py<br/><small>Endpoints</small>"]
        schemas["📝 schemas/schemas.py<br/><small>Validation</small>"]
    end

    subgraph Layer2["⬆️ LAYER 2: BUSINESS LOGIC"]
        direction LR
        service["⚙️ scanner/service.py<br/><small>Orchestration</small>"]
    end

    subgraph Layer3["⬆️ LAYER 3: DATA ACCESS"]
        direction LR
        crud["💾 crud/crud.py<br/><small>DB Operations</small>"]
        parser["📄 scanner/json_parser.py<br/><small>File Operations</small>"]
    end

    subgraph Layer4["⬆️ LAYER 4: INFRASTRUCTURE"]
        direction LR
        models["📋 models/models.py<br/><small>ORM Entities</small>"]
        session["🔌 database/session.py<br/><small>DB Connection</small>"]
        config["⚡ core/config.py<br/><small>Settings</small>"]
    end

    subgraph Layer5["⬆️ LAYER 5: EXTERNAL"]
        direction LR
        postgres[("🐘 PostgreSQL")]
        filesystem[("📁 Filesystem")]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Layer5

    style Layer1 fill:#be185d,stroke:#ec4899,stroke-width:3px,color:#fff
    style Layer2 fill:#7c3aed,stroke:#a855f7,stroke-width:3px,color:#fff
    style Layer3 fill:#4f46e5,stroke:#818cf8,stroke-width:3px,color:#fff
    style Layer4 fill:#0284c7,stroke:#38bdf8,stroke-width:3px,color:#fff
    style Layer5 fill:#0d9488,stroke:#2dd4bf,stroke-width:3px,color:#fff
```

<br>

---

<br>

## 🔗 Module Dependencies

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#06b6d4', 'primaryTextColor': '#e6edf3', 'lineColor': '#a78bfa', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TD
    subgraph Entry["🚀 ENTRY POINT"]
        main["main.py"]
    end

    subgraph Routers["🌐 ROUTERS"]
        core["routers/core.py"]
    end

    subgraph Schemas["📝 SCHEMAS"]
        schemas["schemas/schemas.py"]
    end

    subgraph Services["⚙️ SERVICES"]
        service["scanner/service.py"]
        parser["scanner/json_parser.py"]
    end

    subgraph DataAccess["💾 DATA ACCESS"]
        crud["crud/crud.py"]
    end

    subgraph Models["📋 MODELS"]
        models["models/models.py"]
    end

    subgraph Database["🔌 DATABASE"]
        session["database/session.py"]
        deps["core/deps.py"]
    end

    subgraph Config["⚡ CONFIG"]
        config["core/config.py"]
    end

    main --> core
    main --> config

    core --> schemas
    core --> service
    core --> deps

    service --> crud
    service --> parser
    service --> schemas

    crud --> models
    crud --> schemas

    parser --> config

    deps --> session
    session --> config

    models -.->|"inherits"| Base["DeclarativeBase"]

    style Entry fill:#b45309,stroke:#fbbf24,stroke-width:3px,color:#fff
    style Routers fill:#dc2626,stroke:#f87171,stroke-width:2px,color:#fff
    style Schemas fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff
    style Services fill:#be185d,stroke:#ec4899,stroke-width:2px,color:#fff
    style DataAccess fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff
    style Models fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
    style Database fill:#1d4ed8,stroke:#60a5fa,stroke-width:2px,color:#fff
    style Config fill:#c2410c,stroke:#fb923c,stroke-width:2px,color:#fff
```

<br>

---

<br>

## 🔄 Request Flow

<br>

### 📤 Create Extension Flow

<details>
<summary><strong>🔽 Click to expand sequence diagram</strong></summary>

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#a855f7', 'primaryTextColor': '#e6edf3', 'actorTextColor': '#e6edf3', 'actorBkg': '#7c3aed', 'actorBorder': '#a855f7', 'actorLineColor': '#c084fc', 'signalColor': '#22d3ee', 'signalTextColor': '#e6edf3', 'sequenceNumberColor': '#0d1117', 'noteBkgColor': '#be185d', 'noteTextColor': '#e6edf3', 'noteBorderColor': '#ec4899', 'activationBkgColor': '#4f46e5', 'activationBorderColor': '#818cf8', 'labelBoxBkgColor': '#161b22'}}}%%
sequenceDiagram
    autonumber
    participant C as 👤 Client
    participant R as 🌐 Router
    participant S as ⚙️ Service
    participant P as 📄 Parser
    participant CR as 💾 CRUD
    participant DB as 🐘 PostgreSQL

    C->>R: POST /createExtension {"name": "python"}
    R->>R: Validate ScanRequest
    R->>S: create_extension_by_name(db, "python")

    S->>P: search_extension("python")
    P->>P: Scan extensions/ directory
    P->>P: Parse package.json
    P-->>S: Return package data

    S->>P: parse_capabilities(package_json)
    P-->>S: Return capabilities data
    S->>P: parse_scripts(package_json)
    P-->>S: Return scripts data
    S->>P: parse_activation_events(package_json)
    P-->>S: Return activation events data
    S->>P: parse_contributes(package_json)
    P-->>S: Return contributes data

    S->>S: ExtensionSchema(**package_json)
    S->>S: ExtensionCapabilitiesSchema(**caps)
    S->>S: ExtensionScriptsSchema(**scripts)
    S->>S: ExtensionActivationEventsSchema(**events)
    S->>S: ExtensionContributesSchema(**contribs)
    S->>CR: create_extension(db, schema, caps, scripts, events, contribs)

    CR->>CR: Extension(**schema.model_dump())
    CR->>DB: INSERT INTO extensions
    DB-->>CR: Return with ID
    CR->>CR: ExtensionCapabilities(ext_id, **caps)
    CR->>DB: INSERT INTO extension_capabilities
    CR->>CR: ExtensionScripts(ext_id, **script)
    CR->>DB: INSERT INTO extension_scripts (for each)
    CR->>CR: ExtensionActivationEvents(ext_id, **event)
    CR->>DB: INSERT INTO extension_activation_events (for each)
    CR->>CR: ExtensionContributes(ext_id, **contribs)
    CR->>DB: INSERT INTO extension_contributes
    CR->>DB: INSERT INTO extension_contributes_commands... (child tables)
    CR->>CR: db.commit() + db.refresh()
    CR-->>S: Return Extension ORM

    S-->>R: Return ExtensionDetailSchema
    R-->>C: 200 OK + ExtensionDetailSchema JSON
```

</details>

<br>

### 🔍 Search Extension Flow

<details>
<summary><strong>🔽 Click to expand sequence diagram</strong></summary>

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#06b6d4', 'primaryTextColor': '#e6edf3', 'actorTextColor': '#e6edf3', 'actorBkg': '#0891b2', 'actorBorder': '#22d3ee', 'actorLineColor': '#67e8f9', 'signalColor': '#a78bfa', 'signalTextColor': '#e6edf3', 'sequenceNumberColor': '#0d1117', 'noteBkgColor': '#0d9488', 'noteTextColor': '#e6edf3', 'noteBorderColor': '#2dd4bf', 'activationBkgColor': '#0284c7', 'activationBorderColor': '#38bdf8', 'labelBoxBkgColor': '#161b22'}}}%%
sequenceDiagram
    autonumber
    participant C as 👤 Client
    participant R as 🌐 Router
    participant S as ⚙️ Service
    participant CR as 💾 CRUD
    participant DB as 🐘 PostgreSQL

    C->>R: GET /searchExtension?name=python
    R->>R: Validate SearchRequest
    R->>S: search_extension_by_name(db, "python")

    S->>CR: search_extension_by_name(db, "python")
    CR->>DB: SELECT * FROM extensions<br/>JOIN capabilities, scripts, events, contributes (lazy/eager)
    DB-->>CR: Return row + related data
    CR-->>S: Return Extension ORM (with relationships)

    S-->>R: Return Extension
    R-->>C: 200 OK + ExtensionDetailSchema JSON
```

</details>

<br>

### 🗑️ Delete Extension Flow

<details>
<summary><strong>🔽 Click to expand sequence diagram</strong></summary>

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#ef4444', 'primaryTextColor': '#e6edf3', 'actorTextColor': '#e6edf3', 'actorBkg': '#dc2626', 'actorBorder': '#f87171', 'actorLineColor': '#fca5a5', 'signalColor': '#fb923c', 'signalTextColor': '#e6edf3', 'sequenceNumberColor': '#0d1117', 'noteBkgColor': '#b45309', 'noteTextColor': '#e6edf3', 'noteBorderColor': '#fbbf24', 'activationBkgColor': '#c2410c', 'activationBorderColor': '#fb923c', 'labelBoxBkgColor': '#161b22'}}}%%
sequenceDiagram
    autonumber
    participant C as 👤 Client
    participant R as 🌐 Router
    participant S as ⚙️ Service
    participant CR as 💾 CRUD
    participant DB as 🐘 PostgreSQL

    C->>R: DELETE /deleteExtension?name=python
    R->>R: Validate SearchRequest
    R->>S: delete_extension_by_name(db, "python")

    S->>CR: delete_extension(db, "python")
    CR->>DB: SELECT * FROM extensions WHERE name = 'python'
    DB-->>CR: Return row
    CR->>DB: DELETE FROM extensions WHERE name = 'python'
    DB-->>CR: Confirm Delete (Cascade to all related tables)
    CR->>CR: db.commit()
    CR-->>S: Return True

    S-->>R: Return True
    R-->>C: 200 OK {"message": "deleted"}
```

</details>

<br>

---

<br>

## 🗃️ Database Schema

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#3b82f6', 'primaryTextColor': '#e6edf3', 'lineColor': '#818cf8', 'tertiaryColor': '#4f46e5', 'attributeBackgroundColorEven': '#161b22', 'attributeBackgroundColorOdd': '#21262d'}}}%%
erDiagram
    EXTENSIONS ||--|| EXTENSION_CAPABILITIES : "has (1:1)"
    EXTENSIONS ||--|| EXTENSION_CONTRIBUTES : "has (1:1)"
    EXTENSIONS ||--o{ EXTENSION_SCRIPTS : "contains (1:N)"
    EXTENSIONS ||--o{ EXTENSION_ACTIVATION_EVENTS : "triggers (1:N)"

    EXTENSIONS {
        int id PK "🔑 Auto-increment"
        string name "📇 Indexed, NOT NULL"
        string version "🏷️ Indexed, NOT NULL"
        string publisher "📇 Indexed, NOT NULL"
        jsonb engines "⚙️ NOT NULL"
        string license "📜 Optional"
        string displayName "🏷️ Optional"
        text description "📝 Optional"
        array categories "📂 String Array"
        array keywords "🏷️ String Array"
        jsonb galleryBanner "🎨 Optional"
        boolean preview "👁️ Optional"
        jsonb badges "🏅 Optional"
        text markdown "📖 Optional"
        jsonb qna "❓ Optional"
        jsonb sponsor "💰 Optional"
        string icon "🖼️ Optional"
        string pricing "💵 Optional"
        string main "📄 Entry Point"
        string web "🌐 Optional"
        jsonb dependencies "📦 Optional"
        jsonb devDependencies "🛠️ Optional"
        timestamp created_at "📅 Auto-set"
        timestamp updated_at "🔄 Auto-update"
        array extensionPack "📦 Pack IDs"
        array extensionDependencies "🔗 Dep IDs"
        array extensionKind "🏷️ UI/Workspace"
        jsonb npm_fields "📦 Standard npm"
        jsonb extra_fields "➕ Custom/Unknown"
    }

    EXTENSION_CAPABILITIES {
        int extension_id PK,FK "🔑 Foreign Key"
        enum untrusted_supported "🔒 Security"
        text untrusted_description "📝 Explanation"
        array untrusted_restricted_configurations "🚫 Disabled Settings"
        enum virtual_supported "☁️ Virtual"
        text virtual_description "📝 Explanation"
    }

    EXTENSION_CONTRIBUTES {
        int extension_id PK,FK "🔑 Foreign Key"
        jsonb configuration "⚙️ Settings Schema"
        jsonb debuggers "🐛 Debug Config"
        jsonb languages "🗣️ Language Defs"
        jsonb grammars "📝 TextMate"
        jsonb other_fields "➕ Many JSONB Fields"
    }

    EXTENSION_CONTRIBUTES ||--o{ EXTENSION_CONTRIBUTES_COMMANDS : "has (1:N)"
    EXTENSION_CONTRIBUTES ||--o{ EXTENSION_CONTRIBUTES_KEYBINDINGS : "has (1:N)"
    EXTENSION_CONTRIBUTES ||--o{ EXTENSION_CONTRIBUTES_MENUS : "has (1:N)"

    EXTENSION_CONTRIBUTES_COMMANDS {
        int id PK
        int contributes_id FK
        string command_id "🆔 Command ID"
        string title "🏷️ Display Title"
        string category "📂 Grouping"
        jsonb icon "🖼️ Icon Path"
        jsonb when "❓ Condition"
    }

    EXTENSION_CONTRIBUTES_KEYBINDINGS {
        int id PK
        int contributes_id FK
        string key "🎹 Key Combo"
        string command "⚡ Trigger Command"
        string when "❓ Condition"
    }

    EXTENSION_CONTRIBUTES_MENUS {
        int id PK
        int contributes_id FK
        string menu_location "📍 Location ID"
        string command "⚡ Command"
    }

    EXTENSION_SCRIPTS {
        int id PK "🔑 Auto-increment"
        int extension_id FK "🔗 Foreign Key"
        string script_name "📛 Script Name"
        jsonb script_command "⚡ Command Details"
    }

    EXTENSION_ACTIVATION_EVENTS {
        int id PK "🔑 Auto-increment"
        int extension_id FK "🔗 Foreign Key"
        string event_type "🎯 Event Type (indexed)"
        string event_value "📋 Event Value (nullable)"
    }
```

<br>

### 🔒 Constraints & Indexes

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#ec4899', 'primaryTextColor': '#e6edf3', 'lineColor': '#f472b6', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart LR
    subgraph Constraints["🔒 CONSTRAINTS"]
        PK["🔑 PRIMARY KEY: id"]
        UQ["🔗 UNIQUE: (publisher, name, version)"]
    end

    subgraph Indexes["⚡ INDEXES"]
        IDX1["📇 INDEX: name"]
        IDX2["📇 INDEX: publisher"]
        IDX3["📇 INDEX: version"]
    end

    subgraph Table["📋 extensions"]
        T["Extensions Table"]
    end

    Constraints --> Table
    Indexes --> Table

    style Constraints fill:#dc2626,stroke:#f87171,stroke-width:3px,color:#fff
    style Indexes fill:#b45309,stroke:#fbbf24,stroke-width:3px,color:#fff
    style Table fill:#7c3aed,stroke:#a855f7,stroke-width:3px,color:#fff
```

<br>

---

<br>

## 🐳 Docker Infrastructure

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#0ea5e9', 'primaryTextColor': '#e6edf3', 'lineColor': '#38bdf8', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TB
    subgraph Host["🖥️ HOST MACHINE"]
        subgraph DockerCompose["🐳 Docker Compose"]
            subgraph APIContainer["📦 api container"]
                direction TB
                Python["🐍 Python 3.11-slim"]
                Uvicorn["⚡ Uvicorn Server"]
                AppCode["📄 Application Code"]
                Python --> Uvicorn
                Uvicorn --> AppCode
            end

            subgraph DBContainer["📦 postgres container"]
                direction TB
                PG["🐘 PostgreSQL 16-alpine"]
                Data["💿 Data Directory"]
                PG --> Data
            end

            subgraph ExecutorContainer["📦 executor container"]
                direction TB
                Xvfb["🖥️ Xvfb :99"]
                VSCode["💻 VS Code GUI"]
                Monitor["📡 tcpdump / inotify / strace"]
                NoVNC["🌐 noVNC :6080"]
                Xvfb --> VSCode
                VSCode --> Monitor
                Xvfb --> NoVNC
            end
        end

        subgraph Volumes["💾 VOLUMES"]
            PGData["🔒 postgres_data"]
            AppMount["📁 /app (bind mount)"]
            ExtMount["📦 /extensions-input (read-only)"]
            ResultMount["📁 /results (output)"]
        end

    subgraph Ports["🔌 PORTS"]
        P8000["🌐 localhost:8000 (API)"]
        P5432["🗄️ localhost:5432 (DB)"]
        P6080["🖥️ localhost:6080 (noVNC)"]
    end
    end

    APIContainer <-->|":5432"| DBContainer
    DBContainer --> PGData
    APIContainer --> AppMount
    ExecutorContainer --> ExtMount
    ExecutorContainer --> ResultMount
    P8000 --> APIContainer
    P5432 --> DBContainer
    P6080 --> ExecutorContainer

    style Host fill:#1e293b,stroke:#475569,stroke-width:3px,color:#e6edf3
    style DockerCompose fill:#0891b2,stroke:#22d3ee,stroke-width:3px,color:#fff
    style APIContainer fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff
    style DBContainer fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
    style ExecutorContainer fill:#b91c1c,stroke:#f87171,stroke-width:2px,color:#fff
    style Volumes fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#fff
    style Ports fill:#be185d,stroke:#ec4899,stroke-width:2px,color:#fff
```

<br>

### 📦 Container Details

<br>

<table>
<tr>
<td width="50%">

#### 🔮 API Container

| Property | Value |
|:---------|:------|
| **Base Image** | `python:3.11-slim-bookworm` |
| **User** | `appuser` (non-root) |
| **Port** | `8000 (default, override with API_PORT)` |
| **Command** | `uvicorn main:app` |

</td>
<td width="50%">

#### 🐘 Database Container

| Property | Value |
|:---------|:------|
| **Base Image** | `postgres:16-alpine` |
| **Port** | `5432 → 5432 (default, override with POSTGRES_PORT)` |
| **Healthcheck** | `pg_isready` |
| **Volume** | `postgres_data` |

</td>
</tr>
<tr>
<td colspan="2">

#### 🔬 Executor Container

| Property | Value |
|:---------|:------|
| **Base Image** | `ubuntu:22.04` |
| **User** | `executor` (non-root) |
| **Port** | `6080 (noVNC, override with EXECUTOR_NOVNC_PORT)` |
| **Display** | `Xvfb :99 (1920x1080x24)` |
| **Window Manager** | `openbox` |
| **VNC** | `x11vnc → noVNC (browser access)` |
| **VS Code** | Full GUI, `--no-sandbox` + CDP (`--remote-debugging-port`) |
| **Monitoring** | `tcpdump`, `tshark`, `inotifywait`, `strace` |
| **Capabilities** | `NET_RAW`, `SYS_PTRACE` |
| **Resources** | 4GB RAM, 2 CPUs |
| **Volumes** | `./extensions:/extensions-input:ro`, `./output:/results` |

</td>
</tr>
</table>

<br>

---

<br>

## ⚙️ Configuration Flow

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#f97316', 'primaryTextColor': '#e6edf3', 'lineColor': '#fb923c', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TB
    subgraph Sources["📥 CONFIGURATION SOURCES"]
        ENV["🔐 Environment Variables<br/><small>(Highest Priority)</small>"]
        DOTENV["📄 .env File<br/><small>(Development)</small>"]
        DEFAULT["⚙️ Default Values<br/><small>(Lowest Priority)</small>"]
    end

    subgraph Settings["⚙️ PYDANTIC SETTINGS"]
        Config["core/config.py<br/><small>Settings Class</small>"]
    end

    subgraph Values["📋 CONFIGURATION VALUES"]
        subgraph ProjectVals["📁 Project"]
            PROJECT["📛 PROJECT_NAME<br/><small>'ExTrace API'</small>"]
            ENVMODE["🌍 PROJECT_ENV<br/><small>'dev'</small>"]
            EXTDIR["📁 PROJECT_EXTENSION_DIR<br/><small>'extensions'</small>"]
        end
        subgraph APIVals["🌐 API"]
            API_HOST["🖥️ API_HOST<br/><small>'0.0.0.0'</small>"]
            API_PORT["🔌 API_PORT<br/><small>8000</small>"]
        end
        subgraph DBVals["🐘 Database"]
            DB_URL["🔗 DATABASE_URL<br/><small>(Override)</small>"]
            PG_HOST["🖥️ POSTGRES_HOST<br/><small>'localhost'</small>"]
            PG_PORT["🔌 POSTGRES_PORT<br/><small>5432</small>"]
        end
    end

    subgraph Consumers["👥 CONSUMERS"]
        Session["database/session.py"]
        Parser["scanner/json_parser.py"]
        Main["main.py"]
    end

    ENV --> Config
    DOTENV --> Config
    DEFAULT --> Config

    Config --> ProjectVals
    Config --> APIVals
    Config --> DBVals

    DB_URL --> Session
    PG_HOST --> Session
    EXTDIR --> Parser
    PROJECT --> Main
    API_PORT --> Main

    style Sources fill:#dc2626,stroke:#f87171,stroke-width:3px,color:#fff
    style Settings fill:#7c3aed,stroke:#a855f7,stroke-width:3px,color:#fff
    style Values fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff
    style Consumers fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
```

<br>

---

<br>

## 📁 File Structure

<br>

```text
📂 automation_enviroment/
│
├── 📄 main.py                    # 🚀 Application entry point
├── 🐳 docker-compose.yml         # 📦 Container orchestration
├── 🧰 Makefile                   # Dev/test/lint commands
├── 📋 alembic.ini                # 🔄 Migration configuration
├── 🔐 .env                       # 🔒 Environment variables
│
├── 📁 core/                      # ⚡ Core configuration
│   ├── ⚙️ config.py              # Settings management
│   └── 💉 deps.py                # Dependency injection
│
├── 📁 database/                  # 🔌 Database layer
│   └── 🔗 session.py             # Session factory
│
├── 📁 models/                    # 📋 ORM models
│   └── 🗃️ models.py              # SQLAlchemy entities
│
├── 📁 schemas/                   # 📝 Pydantic schemas
│   └── ✅ schemas.py             # Request/Response validation
│
├── 📁 crud/                      # 💾 Data access
│   └── 🔍 crud.py                # CRUD operations
│
├── 📁 routers/                   # 🌐 API routes
│   ├── 🛤️ core.py                # Main endpoints
│   ├── 🐳 Dockerfile             # API container config
│   └── 📦 requirements.txt       # Python dependencies
│
├── 📁 scanner/                   # ⚙️ Business logic
│   ├── 🎯 service.py             # Service orchestration
│   └── 📄 json_parser.py         # File parsing utilities
│
├── 📁 alembic/                   # 🔄 Migrations
│   ├── 🌍 env.py                 # Migration environment
│   └── 📁 versions/              # Migration scripts
│
├── 📁 executor/                  # 🔬 Dynamic analysis
│   ├── 🐳 Dockerfile             # Ubuntu 22.04 + VS Code + Xvfb + monitoring
│   ├── 🚀 start.sh              # Entrypoint: Xvfb, openbox, VNC, noVNC
│   └── 📄 __init__.py           # Package init
│
├── 📁 documents/                 # 📚 Architecture, testing, reviews
│   └── ...
│
├── 📁 extensions/                # 📦 Extension storage (mounted read-only in executor)
│   └── 📂 publisher.ext-1.0.0/   # Unpacked extensions
│
└── 📁 output/                    # 📁 Analysis results (mounted in executor as /results)
```

<br>

---

<br>

## 📜 Architectural Rules

<br>

### ✅ Allowed Dependencies

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#22c55e', 'primaryTextColor': '#e6edf3', 'lineColor': '#4ade80', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TD
    R["🌐 Router"] -->|"✅ can call"| S["⚙️ Service"]
    S -->|"✅ can call"| C["💾 CRUD"]
    S -->|"✅ can call"| P["📄 Parser"]
    C -->|"✅ can use"| M["📋 Model"]

    style R fill:#15803d,stroke:#22c55e,stroke-width:3px,color:#fff
    style S fill:#059669,stroke:#10b981,stroke-width:3px,color:#fff
    style C fill:#0d9488,stroke:#14b8a6,stroke-width:3px,color:#fff
    style P fill:#0891b2,stroke:#06b6d4,stroke-width:3px,color:#fff
    style M fill:#0284c7,stroke:#0ea5e9,stroke-width:3px,color:#fff
```

<br>

### ❌ Forbidden Dependencies

> [!CAUTION]
> The following dependencies are **strictly prohibited** to maintain clean architecture.

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#ef4444', 'primaryTextColor': '#e6edf3', 'lineColor': '#f87171', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TD
    R["🌐 Router"] -.->|"❌ direct DB call"| C["💾 CRUD"]
    R -.->|"❌ file operations"| P["📄 Parser"]
    C -.->|"❌ business logic"| S["⚙️ Service"]
    M["📋 Model"] -.->|"❌ API calls"| R

    style R fill:#b91c1c,stroke:#ef4444,stroke-width:3px,color:#fff
    style S fill:#c2410c,stroke:#f97316,stroke-width:3px,color:#fff
    style C fill:#b45309,stroke:#f59e0b,stroke-width:3px,color:#fff
    style P fill:#a16207,stroke:#eab308,stroke-width:3px,color:#fff
    style M fill:#854d0e,stroke:#facc15,stroke-width:3px,color:#fff
```

<br>

### 📊 Responsibility Matrix

<br>

| Component | HTTP | Business Logic | DB Operations | File I/O | Validation |
|:----------|:----:|:--------------:|:-------------:|:--------:|:----------:|
| **🌐 Router** | ✅ | ❌ | ❌ | ❌ | ✅ `request` |
| **⚙️ Service** | ❌ | ✅ | ❌ `via CRUD` | ❌ `via Parser` | ✅ `business` |
| **💾 CRUD** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **📄 Parser** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **📋 Model** | ❌ | ❌ | ✅ `schema` | ❌ | ❌ |

<br>

---

<br>

## 🔮 Future Architecture

> [!TIP]
> Planned enhancements for the ExTrace security analysis platform.

<br>

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#8b5cf6', 'primaryTextColor': '#e6edf3', 'lineColor': '#a78bfa', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
flowchart TB
    subgraph Current["🟢 CURRENT IMPLEMENTATION"]
        R1["🌐 Router"]
        S1["⚙️ Service"]
        C1["💾 CRUD"]
        P1["📄 JSON Parser"]
    end

    subgraph Future["🔮 PLANNED ADDITIONS"]
        subgraph Analyzers["🔍 ANALYZERS"]
            PA["🔐 Permission Analyzer"]
            CA["💻 Code Analyzer"]
            RC["⚠️ Risk Calculator"]
        end

        subgraph Reporters["📊 REPORTERS"]
            JR["📄 JSON Reporter"]
            HR["🌐 HTML Reporter"]
        end

        subgraph Executor["⚡ EXECUTOR"]
            SB["🖥️ Xvfb + VS Code GUI"]
            DC["🐳 Docker Controller"]
            MN["📡 Monitors (net/fs/proc)"]
        end
    end

    S1 --> Analyzers
    Analyzers --> RC
    RC --> Reporters
    S1 --> Executor

    style Current fill:#15803d,stroke:#22c55e,stroke-width:3px,color:#fff
    style Future fill:#7c3aed,stroke:#a855f7,stroke-width:3px,color:#fff
    style Analyzers fill:#be185d,stroke:#ec4899,stroke-width:2px,color:#fff
    style Reporters fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff
    style Executor fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#fff
```

<br>

---

<br>

## 📋 Quick Reference

<br>

### 🌐 Endpoint Summary

<br>

| Method | Endpoint | Query Params | Handler | Service Function |
|:------:|:---------|:-------------|:--------|:-----------------|
| 🟢 `GET` | `/` | — | `read_root()` | — |
| 🟢 `GET` | `/health` | — | `health_check()` | — |
| 🔵 `GET` | `/searchExtension` | `name`, `publisher?`, `version?` | `search_extension()` | `search_extension_by_name()` |
| 🔵 `GET` | `/getExtensionsBaseInfo` | — | `get_extensions_base_info()` | `get_all_extensions_basic()` |
| 🔵 `GET` | `/getExtensionsAllInfo` | `skip?`, `limit?` | `get_extensions_all_info()` | `get_all_extensions_all()` |
| 🟣 `POST` | `/createExtension` | — | `create_extension()` | `create_extension_by_name()` |
| 🔴 `DELETE` | `/deleteExtension` | `name`, `publisher?`, `version?` | `delete_extension()` | `delete_extension_by_name()` |
| 🔵 `GET` | `/getExtensionScripts` | `name`, `publisher?`, `version?` | `get_extension_scripts()` | `get_extension_scripts()` |
| 🔵 `GET` | `/getExtensionActivationEvents` | `name`, `publisher?`, `version?` | `get_extension_activation_events()` | `get_extension_activation_events()` |
| 🔵 `GET` | `/getExtensionCapabilities` | `name`, `publisher?`, `version?` | `get_extension_capabilities()` | `get_extension_capabilites()` |
| 🔵 `GET` | `/getExtensionContributesAll` | `name`, `publisher?`, `version?` | `get_extension_contributes_all()` | `get_extension_contributes_all()` |
| 🔵 `GET` | `/getExtensionContributesCommands` | `name`, `publisher?`, `version?` | `get_extension_contributes_commands()` | `get_extension_contributes_commands()` |

<br>

### 🛠️ Technology Stack

<br>

| Component | Technology | Version | Status |
|:----------|:-----------|:-------:|:------:|
| **⚡ Framework** | FastAPI | `≥0.100.0` | 🟢 Active |
| **🚀 Server** | Uvicorn | `≥0.20.0` | 🟢 Active |
| **🗃️ ORM** | SQLAlchemy | `≥2.0.0` | 🟢 Active |
| **🔄 Migrations** | Alembic | `≥1.10.0` | 🟢 Active |
| **✅ Validation** | Pydantic | `≥2.0.0` | 🟢 Active |
| **🐘 Database** | PostgreSQL | `16` | 🟢 Active |
| **🐳 Container** | Docker Compose | `—` | 🟢 Active |
| **🐍 Python** | CPython | `3.11` | 🟢 Active |
| **🎭 Playwright** | Playwright for Python | `latest` | 🟢 Active |
| **🖥️ Xvfb** | Virtual Framebuffer | `—` | 🟢 Active |
| **🔌 noVNC** | Browser VNC Client | `—` | 🟢 Active |

<br>

---

<br>

## 🎭 Executor: Playwright UI Automation

> [!NOTE]
> Full documentation: [`documents/EXECUTOR_PLAYWRIGHT.md`](EXECUTOR_PLAYWRIGHT.md)

The executor container runs VS Code with a virtual display (Xvfb) and provides Playwright-based UI automation for triggering extension activation events.

<br>

### Container Startup Flow

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant S as start.sh
    participant X as Xvfb
    participant W as workspace.py
    participant V as VS Code
    participant N as noVNC

    S->>X: Start virtual display :99
    S->>S: Start Openbox + x11vnc
    S->>W: Setup honeypot environment
    W->>W: Create /workspace files (.env, src/, credentials/)
    W->>W: Create ~/.ssh, ~/.aws, ~/.kube, ~/.docker
    S->>S: Write VS Code settings (trust=off)
    S->>V: Launch VS Code /workspace (CDP:9222)
    S->>N: Start noVNC (port 6080)
```

<br>

### Playwright Module Architecture

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TD
    EP[entrypoint.py] --> VS[vscode.py<br/>CDP Connection]
    EP --> CMD[commands.py<br/>Command Palette]
    EP --> ED[editor.py<br/>Editor Ops]
    EP --> SB[sidebar.py<br/>Activity Bar]
    EP --> TM[terminal.py<br/>Terminal]
    EP --> PN[panel.py<br/>Bottom Panel]

    CMD --> KB[keyboard.py<br/>Shortcut Constants]
    ED --> KB
    ED --> CMD
    SB --> KB
    SB --> CMD
    TM --> KB
    TM --> CMD
    PN --> KB
    PN --> CMD

    WS[workspace.py<br/>Honeypot + FS] -.->|start.sh| VS

    style KB fill:#7c3aed,color:#fff
    style WS fill:#059669,color:#fff
    style VS fill:#2563eb,color:#fff
```

<br>

### Honeypot Coverage

| Target | Location | Files |
|:-------|:---------|:------|
| **Environment** | `/workspace/` | `.env`, `.env.production`, `.env.local` |
| **SSH** | `~/.ssh/` | `id_rsa` (600), `id_rsa.pub`, `config` |
| **AWS** | `~/.aws/` | `credentials`, `config` |
| **Kubernetes** | `~/.kube/` | `config` (cluster token) |
| **Docker** | `~/.docker/` | `config.json` (registry auth) |
| **GCP/Firebase** | `/workspace/credentials/` | Service account JSONs |
| **Git** | `~/` | `.gitconfig`, `.git-credentials` |
| **NPM** | `~/` | `.npmrc` (auth tokens) |
| **Source Code** | `/workspace/src/` | Hardcoded secrets in Python |
| **Infra** | `/workspace/infra/` | Terraform vars, docker-compose |
| **Shell History** | `~/` | `.bash_history`, `.python_history` |
| **Crypto** | `/workspace/.wallet/` | Ethereum keystore |

<br>

---

<br>

<div align="center">

### 📝 Documentation Notice

<br>

> *This document should be updated when significant architectural changes are made.*

<br>

**Made with 💜 for VS Code Extension Security**

<br>

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)

</div>
