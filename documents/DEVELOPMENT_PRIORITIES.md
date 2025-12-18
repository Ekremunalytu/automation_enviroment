<div align="center">

# 🎯 ExTrace - Development Priorities

<br>

**Roadmap & Implementation Strategy**

<br>

[![Document Type](https://img.shields.io/badge/Type-Roadmap-7c3aed?style=for-the-badge&logo=readthedocs&logoColor=white)](https://github.com/yourusername/extrace)
[![Last Updated](https://img.shields.io/badge/Updated-2025--12--11-059669?style=for-the-badge&logo=calendar&logoColor=white)](https://github.com/yourusername/extrace)
[![Status](https://img.shields.io/badge/Status-Active_Development-0891b2?style=for-the-badge&logo=activity&logoColor=white)](https://github.com/yourusername/extrace)

<br>

---

`Current Sprint: Identity & Deep Parsing` • `Next: Risk Analysis`

---

</div>

<br>

## 📌 Current Focus: Extension Identity

> [!IMPORTANT]
> The immediate priority is building **comprehensive parsers** to extract the complete identity and behavioral fingerprint of VS Code extensions. Analysis and risk scoring will follow in subsequent sprints.

<br>

---

<br>

## 🚀 Phase 1: Deep Parsing

### 1.1 Manifest Parser Enhancement

**Goal:** Extract every field from `package.json` that reveals extension behavior.

| Field Category | Fields to Parse | Purpose | Status |
|:---------------|:----------------|:--------|:-------|
| **Identity** | `name`, `publisher`, `version`, `displayName` | Unique extension identification | ✅ Done |
| **Permissions** | `activationEvents`, `contributes` | What triggers the extension | 🚧 In Progress |
| **Entry Points** | `main`, `browser`, `web` | Code execution locations | ✅ Done |
| **Dependencies** | `dependencies`, `devDependencies`, `extensionDependencies` | Supply chain mapping | ⏳ Pending |
| **Capabilities** | `capabilities`, `extensionKind` | Extension type classification | ✅ Done |
| **Scripts** | `scripts` | npm scripts parsing | ✅ Done |
| **Repository** | `repository`, `homepage`, `bugs` | Source verification | ⏳ Pending |

<br>

### 1.2 Database Schema Expansion

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#7c3aed', 'primaryTextColor': '#e6edf3', 'lineColor': '#22d3ee', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
erDiagram
    EXTENSIONS ||--o{ COMMANDS : has
    EXTENSIONS ||--|| CAPABILITIES : has
    EXTENSIONS ||--o{ EVENTS : triggers
    EXTENSIONS ||--o{ CONTRIBS : provides
    EXTENSIONS ||--o{ DEPS : depends_on
    EXTENSIONS ||--o{ SCRIPTS : contains

    EXTENSIONS {
        int id PK
        string name
    }

    CAPABILITIES {
        enum untrusted_supported
        enum virtual_supported
    }

    COMMANDS {
        string command_id
        string title
        jsonb when
    }

    EVENTS {
        string event_type
        string event_value
    }

    CONTRIBS {
        string type
        jsonb data
    }

    DEPS {
        string dep_name
        string version
    }

    SCRIPTS {
        string script_name
        jsonb script_command
    }
```

<br>

### 1.3 Activation Event Analysis

**Goal:** Understand when and why an extension activates.

| Event Type | Risk Level | Description |
|:-----------|:-----------|:------------|
| `*` | 🔴 **High** | Always active (potential performance/security impact) |
| `onStartupFinished` | 🟡 **Medium** | Runs at VS Code startup |
| `onUri` | 🟡 **Medium** | Can be triggered externally |
| `onFileSystem:*` | 🟡 **Medium** | File access triggers |
| `onCommand:*` | 🟢 **Low** | Only on explicit user action |
| `onLanguage:*` | 🟢 **Low** | When opening specific file types |

<br>

### 1.4 Contribution Point Mapping

**Goal:** Map all extension contributions to understand capabilities.

<details>
<summary><strong>📋 View Contribution Types</strong></summary>

- `languages` - Language support declarations
- `grammars` - Syntax highlighting
- `themes` - Color themes
- `snippets` - Code snippets
- `views` - Custom views/panels
- `viewsContainers` - View containers
- `configuration` - Settings contributions
- `configurationDefaults` - Default settings
- `taskDefinitions` - Task types
- `problemMatchers` - Error patterns
- `debuggers` - Debug adapters
- `breakpoints` - Breakpoint types
- `terminal` - Terminal profiles
- `walkthroughs` - Onboarding flows

</details>

<br>

---

<br>

## 🔮 Phase 2: Analysis (Future)

> [!WARNING]
> This phase begins **AFTER** Phase 1 completion.

1.  **Risk Scoring Engine**
    *   Pattern-based risk detection
    *   Permission analysis
    *   Behavioral classification

2.  **Code Analysis**
    *   JavaScript/TypeScript static analysis
    *   API call detection
    *   Network request patterns

3.  **Comparison & Diff**
    *   Version comparison
    *   Regression identification

<br>

---

<br>

## 📋 Implementation Tasks

### 🗄️ Database Tasks
- [ ] Create `extension_activation_events` table
- [ ] Create `extension_commands` table
- [ ] Create `extension_contributions` table
- [ ] Create `extension_dependencies` table
- [ ] Generate Alembic migrations
- [ ] Update SQLAlchemy models

### ⚙️ Parser Tasks
- [ ] Create `manifest_parser.py` - Full package.json parsing
- [ ] Create `activation_parser.py` - Activation event extraction
- [ ] Create `command_parser.py` - Command detection
- [ ] Create `contribution_parser.py` - Contribution point mapping
- [ ] Create `dependency_parser.py` - Dependency analysis

### 🔄 Service & Schema Tasks
- [ ] Update `service.py` with new parsers
- [ ] Create CRUD functions for new tables
- [ ] Add API endpoints for querying parsed data
- [ ] Create Pydantic schemas for new data structures

<br>

---

<br>

## 🚦 Implementation Order

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'background': '#0d1117', 'primaryColor': '#be185d', 'primaryTextColor': '#e6edf3', 'lineColor': '#f472b6', 'mainBkg': '#161b22', 'nodeBkg': '#21262d', 'clusterBkg': '#161b22'}}}%%
graph LR
    C[("1. Commands\n(High Priority)")] --> E[("2. Events\n(Trigger Analysis)")]
    E --> CT[("3. Contributions\n(Capability Mapping)")]
    CT --> D[("4. Dependencies\n(Supply Chain)")]

    style C fill:#be185d,stroke:#ec4899,stroke-width:2px,color:#fff
    style E fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff
    style CT fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff
    style D fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
```

<br>

---

<br>

## ✅ Success Criteria

Phase 1 is complete when:
- ✅ All new database tables created and migrated
- ✅ Parsers extract all specified data from package.json
- ✅ API endpoints expose parsed data
- ✅ Test coverage for all parsers
- ✅ Sample extensions fully parsed and stored

<div align="center">
  <strong>Phase 1 Target: Q1 2026</strong>
</div>
