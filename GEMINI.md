# ExTrace - VS Code Extension Security Analysis

## Project Overview

ExTrace is a security analysis platform designed to **dynamically analyze** and **monitor** VS Code extensions in an isolated sandbox. It focuses on capturing runtime behavior (network, filesystem, processes) to detect malicious activities.

**Core Capabilities:**

1. **Ingest:** Scans first-level extension directories and extracts metadata from `package.json` using exact name match.
2. **Execute:** Runs extensions in a fully-featured VS Code GUI instance within a Docker container.
3. **Monitor:** Captures real-time telemetry using `tcpdump` (network), `inotifywait` (filesystem), and `strace` (system calls).
4. **Visualize:** Provides live browser-based access to the analysis environment via `noVNC`.
5. **Store:** Persists metadata and captured behavioral events in PostgreSQL.

## Tech Stack

* **Language:** Python 3.11+
* **Framework:** FastAPI (with Uvicorn)
* **Database:** PostgreSQL 16
* **ORM:** SQLAlchemy 2.0 (Sync)
* **Infrastructure:** Docker & Docker Compose
* **Dynamic Analysis:**
  * **OS:** Ubuntu 22.04 (in Docker)
  * **Display:** Xvfb (Virtual Framebuffer) + Openbox
  * **Remote Access:** x11vnc + noVNC (Port 6080)
  * **Monitoring:** tcpdump, tshark, inotify-tools, strace, xdotool

## Architecture

The project follows a **layered architecture** with a specialized execution engine:

1. **Presentation Layer (`routers/`)**: FastAPI endpoints for management and analysis control.
2. **Business Layer (`scanner/`, `executor/`)**:
    * `scanner/service.py`: Metadata ingestion and database orchestration.
    * `scanner/json_parser.py`: Reads and parses `package.json` files from `extensions/` directory.
    * `executor/`: Logic for managing the dynamic analysis lifecycle (Planned).
3. **Data Access Layer (`crud/`)**: SQLAlchemy-based database interactions.
4. **Infrastructure Layer (`models/`, `database/`)**: Database schemas and connection management.

**Data Flow:**
`Request -> Router -> Service -> Executor (Docker/Xvfb) -> Telemetry Capture -> Database`

## Key Directories

* `executor/`: Dynamic analysis orchestration.
  * `Dockerfile`: Ubuntu 22.04 + VS Code + Xvfb + Monitoring tools.
  * `start.sh`: Entrypoint for the virtual display and VNC stack.
* `extensions/`: Input directory for unpacked VS Code extensions (Read-only mount).
* `output/`: Directory for raw analysis results and logs.
* `scanner/`: Logic for parsing `package.json` metadata.
* `routers/`: API route definitions.
* `models/`: SQLAlchemy database models.
* `schemas/`: Pydantic models for validation.
* `documents/`: Detailed architecture, testing, and roadmap documentation.

## Development Workflow

### Prerequisites

* Docker & Docker Compose
* Python 3.11+

### Common Commands (via `Makefile`)

* **Setup:** `make install-dev` | `make install-hooks`
* **Running API:** `make dev` (local) | `make up` (containerized stack)
* **Executor Management:**
  * `make exec-build`: Build the analysis image.
  * `make exec-up`: Start the virtual display environment.
  * `make exec-shell`: Access the running sandbox.
  * `make exec-test`: Verify VS Code and monitoring tools in the container.
* **Testing:** `make test` | `make check-all` (lint + typecheck + test)
* **Database:** `make migrate` | `make migrate-create`

## Roadmap Status

* **Phase 0 (Completed):** Metadata ingestion system (DB, CRUD, Parsing, API).
* **Phase 1 (Active):** Dynamic Analysis Core. Full GUI VS Code execution in Docker via Xvfb. Honeypot environment and Playwright automation are functional. Telemetry capture (network/fs) is in prototype stage.
* **Phase 2 (Future):** Persona-based simulation, screenshot/screen recording capture, anti-fingerprinting measures, and risk scoring engine.

## Development Conventions

* **Logic over Syntax:** Focus on capturing behavior (dynamic) rather than code patterns (static).
* **Isolation:** All extension code MUST run inside the `executor` container.
* **Type Safety:** Strict `mypy` and `ruff` enforcement.
* **Telemetry:** Prefer raw event capture (pcap, inotify logs) for post-processing.
