<div align="center">

# 🧪 ExTrace Test Documentation

<br>

**Comprehensive Testing Guide for the ExTrace Platform**

<br>

[![pytest](https://img.shields.io/badge/pytest-8.0+-009688?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Coverage](https://img.shields.io/badge/Coverage-Enabled-success?style=for-the-badge&logo=codecov&logoColor=white)](https://codecov.io)

<br>

---

`Last Updated: 2025-12-20` • `Version: 1.0.0` • `Status: Active`

---

</div>

<br>

## 📑 Table of Contents

<details>
<summary><strong>🗂️ Click to expand navigation</strong></summary>

<br>

| Section | Description |
|:--------|:------------|
| [🏗️ Test Infrastructure](#️-test-infrastructure) | Database setup and test isolation |
| [📁 Test Structure](#-test-structure) | Directory organization and files |
| [🔧 Fixtures](#-fixtures) | Pytest fixtures and configuration |
| [📊 Test Coverage](#-test-coverage) | Module-by-module coverage details |
| [🚀 Running Tests](#-running-tests) | Commands and options |
| [🔄 CI Pipeline](#-ci-pipeline) | GitHub Actions integration |
| [📝 Writing Tests](#-writing-tests) | Best practices and guidelines |

</details>

<br>

---

<br>

## 🏗️ Test Infrastructure

> [!NOTE]
> ExTrace uses **PostgreSQL** for all tests to properly support PostgreSQL-specific features like `JSONB` and `ARRAY` types used in the models.

<br>

### Database Configuration

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#7c3aed', 'primaryTextColor': '#e6edf3', 'lineColor': '#22d3ee'}}}%%
flowchart LR
    subgraph Local["🖥️ LOCAL DEVELOPMENT"]
        LocalDB[("PostgreSQL\n:5434")]
    end

    subgraph CI["☁️ CI ENVIRONMENT"]
        CIDB[("PostgreSQL\n:5432")]
    end

    subgraph Tests["🧪 TEST SUITE"]
        Pytest["pytest"]
    end

    Tests --> |"DATABASE_URL"| Local
    Tests --> |"DATABASE_URL"| CI

    style Local fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
    style CI fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff
    style Tests fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff
```

<br>

| Environment | Database URL | Port |
|:------------|:-------------|:-----|
| **Local** | `postgresql://postgres:postgres@localhost:5434/test_db` | 5434 |
| **CI (GitHub Actions)** | `postgresql://postgres:postgres@localhost:5432/test_db` | 5432 |

<br>

### Test Isolation Strategy

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#ec4899', 'primaryTextColor': '#e6edf3', 'lineColor': '#f472b6'}}}%%
sequenceDiagram
    autonumber
    participant T as 🧪 Test
    participant S as 📋 Session
    participant TX as 🔄 Transaction
    participant DB as 🐘 PostgreSQL

    T->>S: Request db_session fixture
    S->>TX: BEGIN TRANSACTION
    TX->>DB: Execute test queries
    DB-->>TX: Return results
    TX-->>S: Test completes
    S->>TX: ROLLBACK ⬅️ All changes reverted
    TX-->>DB: Database unchanged
```

> [!IMPORTANT]
> Each test runs in its own transaction that is **rolled back** after the test completes. This ensures complete test isolation without any data persistence between tests.

<br>

---

<br>

## 📁 Test Structure

<br>

```
📂 tests/
│
├── 📄 __init__.py              # Test package marker
├── ⚙️ conftest.py              # Fixtures and configuration
├── 🏥 test_health.py           # Health check and smoke tests
│
├── 📁 crud/                    # CRUD operation tests
│   ├── 📄 __init__.py
│   └── 🧪 test_crud.py         # create, search, delete tests
│
├── 📁 routers/                 # API endpoint tests
│   ├── 📄 __init__.py
│   └── 🧪 test_core.py         # All router endpoints
│
├── 📁 schemas/                 # Pydantic validation tests
│   ├── 📄 __init__.py
│   └── 🧪 test_schemas.py      # Schema validation tests
│
└── 📁 scanner/                 # Scanner module tests
    ├── 📄 __init__.py
    └── 🧪 test_json_parser.py  # Parser tests with mocking
```

<br>

---

<br>

## 🔧 Fixtures

<br>

### Core Fixtures

<table>
<tr>
<td width="50%">

#### 🔌 `test_engine`

**Scope:** Session

Creates a PostgreSQL engine for the entire test session.

```python
@pytest.fixture(scope="session")
def test_engine() -> Any:
    """Create test database engine."""
    database_url = get_test_database_url()
    engine = create_engine(
        database_url,
        poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
```

</td>
<td width="50%">

#### 📋 `db_session`

**Scope:** Function

Creates a new session with transaction rollback.

```python
@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator:
    """Create session with rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()

    session = sessionmaker(bind=connection)()
    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

</td>
</tr>
<tr>
<td width="50%">

#### 🌐 `client`

**Scope:** Function

FastAPI TestClient with database override.

```python
@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create test client."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

</td>
<td width="50%">

#### 📦 `sample_extension_data`

**Scope:** Function

Sample extension data for testing.

```python
@pytest.fixture
def sample_extension_data() -> dict:
    """Sample extension data."""
    return {
        "name": "test-extension",
        "version": "1.0.0",
        "publisher": "test-publisher",
        "engines": {"vscode": "^1.80.0"},
        "displayName": "Test Extension",
        "description": "A test extension",
        "categories": ["Testing"],
        "keywords": ["test", "sample"],
    }
```

</td>
</tr>
</table>

<br>

---

<br>

## 📊 Test Coverage

<br>

### Module Coverage Summary

| Module | Test File | Test Count | Coverage Areas |
|:-------|:----------|:-----------|:---------------|
| `crud/crud.py` | `test_crud.py` | 4 | create, search, delete, duplicate handling |
| `routers/core.py` | `test_core.py` | 8 | All endpoints, error handling, mocking |
| `schemas/schemas.py` | `test_schemas.py` | 2 | Validation, required fields |
| `scanner/json_parser.py` | `test_json_parser.py` | 4 | File I/O, error handling, mocking |
| Health endpoints | `test_health.py` | 5 | Root, docs, OpenAPI, list endpoints |

<br>

### Detailed Test Descriptions

<details>
<summary><strong>💾 CRUD Tests (test_crud.py)</strong></summary>

<br>

| Test | Description |
|:-----|:------------|
| `test_create_extension` | Creates extension and verifies ID assignment |
| `test_create_duplicate_extension` | Verifies `ValueError` on duplicate publisher+name+version |
| `test_search_extension_by_name` | Tests search functionality and not-found case |
| `test_delete_extension` | Tests deletion and subsequent search returns None |

</details>

<details>
<summary><strong>🌐 Router Tests (test_core.py)</strong></summary>

<br>

| Test | Description |
|:-----|:------------|
| `test_read_root` | Verifies root endpoint returns project info |
| `test_health_check` | Verifies `/health` returns OK status |
| `test_search_extension_endpoint` | Tests `GET /searchExtension` with valid name |
| `test_search_extension_not_found` | Tests 404 response for missing extension |
| `test_delete_extension_endpoint` | Tests `DELETE /deleteExtension` |
| `test_create_extension_endpoint` | Tests `POST /createExtension` with mocked service |
| `test_create_extension_not_found` | Tests 404 when extension not on disk |
| `test_create_extension_conflict` | Tests 409 on duplicate extension |

</details>

<details>
<summary><strong>📝 Schema Tests (test_schemas.py)</strong></summary>

<br>

| Test | Description |
|:-----|:------------|
| `test_extension_schema_valid` | Validates correct schema creation |
| `test_extension_schema_missing_field` | Verifies `ValidationError` for missing required fields |

</details>

<details>
<summary><strong>📄 Parser Tests (test_json_parser.py)</strong></summary>

<br>

| Test | Description |
|:-----|:------------|
| `test_get_package_json_success` | Tests successful JSON file reading with mocking |
| `test_get_package_json_not_found` | Tests behavior when file doesn't exist |
| `test_get_package_json_invalid_json` | Tests handling of malformed JSON |
| `test_search_extension_found` | Tests extension search with mocked filesystem |
| `test_search_extension_dir_not_found` | Tests when extensions directory is missing |

</details>

<br>

---

<br>

## 🚀 Running Tests

<br>

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/crud/test_crud.py

# Run specific test function
pytest tests/crud/test_crud.py::test_create_extension

# Run tests matching pattern
pytest -k "search"
```

<br>

### Coverage Commands

```bash
# Run with coverage report (terminal)
pytest --cov --cov-report=term-missing

# Run with HTML coverage report
pytest --cov --cov-report=html
# Open htmlcov/index.html in browser

# Run with XML coverage (for CI)
pytest --cov --cov-report=xml
```

<br>

### Test Database Setup (Local)

> [!TIP]
> The test database runs on port **5434** to avoid conflicts with the development database on port 5433.

```bash
# Start test database container
docker run -d \
  --name extrace-test-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=test_db \
  -p 5434:5432 \
  postgres:16-alpine

# Verify connection
psql -h localhost -p 5434 -U postgres -d test_db

# Stop and remove
docker stop extrace-test-db && docker rm extrace-test-db
```

<br>

---

<br>

## 🔄 CI Pipeline

<br>

### GitHub Actions Workflow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#06b6d4', 'primaryTextColor': '#e6edf3', 'lineColor': '#22d3ee'}}}%%
flowchart TB
    subgraph Trigger["🎯 TRIGGERS"]
        Push["Push to main/develop/feature/**"]
        PR["Pull Request"]
    end

    subgraph Parallel["⚡ PARALLEL JOBS"]
        Lint["🔍 Lint\nruff check/format"]
        TypeCheck["🔬 Type Check\nmypy"]
    end

    subgraph Sequential["📋 SEQUENTIAL JOBS"]
        Test["🧪 Test\npytest + coverage"]
        Build["🏗️ Build Check\nimport verification"]
    end

    Trigger --> Parallel
    Parallel --> Sequential

    style Trigger fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#fff
    style Parallel fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff
    style Sequential fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
```

<br>

### CI Job Details

| Job | Dependencies | Description |
|:----|:-------------|:------------|
| 🔍 `lint` | None | Ruff linting and format check |
| 🔬 `type-check` | None | mypy type checking |
| 🧪 `test` | lint, type-check | pytest with PostgreSQL service |
| 🏗️ `build` | lint, type-check | Import verification |
| 🪝 `pre-commit` | None (PR only) | Pre-commit hooks check |

<br>

### PostgreSQL Service in CI

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

<br>

---

<br>

## 📝 Writing Tests

<br>

### Test Naming Convention

```python
def test_<action>_<target>_<condition>():
    """
    Test [action] when [condition].

    Examples:
    - test_create_extension_success
    - test_search_extension_not_found
    - test_delete_extension_already_deleted
    """
    pass
```

<br>

### Test Structure (Arrange-Act-Assert)

```python
def test_search_extension_by_name(db_session: Session):
    # Arrange: Setup test data
    schema = ExtensionSchema(
        name="search-me",
        publisher="search-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"}
    )
    create_extension(db_session, schema)

    # Act: Perform the action
    result = search_extension_by_name(db_session, "search-me")

    # Assert: Verify the result
    assert result is not None
    assert result.publisher == "search-pub"
```

<br>

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock

def test_create_extension_endpoint(client: TestClient, db_session: Session):
    """Test POST /createExtension with mocked service."""
    mock_ext = ExtensionSchema(
        name="new-ext",
        publisher="new-pub",
        version="2.0.0",
        engines={"vscode": "^1.0.0"}
    )

    # Mock filesystem operations
    with patch("scanner.service.create_extension_by_name") as mock_create:
        mock_create.return_value = mock_ext

        response = client.post("/createExtension", json={"name": "new-ext"})

        assert response.status_code == 200
        mock_create.assert_called_once()
```

<br>

### Custom Markers

```python
import pytest

@pytest.mark.slow
def test_large_dataset_processing():
    """Long-running test."""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Integration test requiring external services."""
    pass
```

Run specific markers:
```bash
pytest -m "not slow"      # Skip slow tests
pytest -m integration     # Run only integration tests
```

<br>

---

<br>

## 📋 Quick Reference

<br>

| Command | Description |
|:--------|:------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest --lf` | Run last failed tests |
| `pytest -k "name"` | Run tests matching pattern |
| `pytest --cov` | Run with coverage |
| `make test` | Run tests via Makefile |
| `make test-cov` | Run with coverage via Makefile |

<br>

---

<div align="center">

**Built with ❤️ for reliable testing**

</div>
