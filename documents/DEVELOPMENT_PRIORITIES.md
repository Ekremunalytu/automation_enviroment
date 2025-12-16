# ExTrace - Current Development Priorities

> **Document Type:** Development Roadmap  
> **Last Updated:** 2025-12-11  
> **Status:** Active Development

---

## 🎯 Current Sprint: Extension Identity & Deep Parsing

The immediate priority is building comprehensive parsers to extract the complete identity and behavioral fingerprint of VS Code extensions. Analysis and risk scoring will follow in subsequent sprints.

---

## Phase 1: Deep Parsing (Current Focus)

### 1.1 Manifest Parser Enhancement

**Goal:** Extract every field from `package.json` that reveals extension behavior.

| Field Category | Fields to Parse | Purpose |
|---------------|-----------------|---------|
| **Identity** | name, publisher, version, displayName | Unique extension identification |
| **Permissions** | activationEvents, contributes | What triggers the extension |
| **Entry Points** | main, browser, web | Code execution locations |
| **Dependencies** | dependencies, devDependencies, extensionDependencies | Supply chain mapping |
| **Capabilities** | capabilities, extensionKind | Extension type classification |
| **Repository** | repository, homepage, bugs | Source verification |

**New Database Tables Required:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    extension_activation_events                       │
├─────────────────────────────────────────────────────────────────────┤
│ id              │ SERIAL PRIMARY KEY                                │
│ extension_id    │ FK → extensions.id                                │
│ event_type      │ VARCHAR (onCommand, onLanguage, onUri, etc.)      │
│ event_value     │ VARCHAR (specific trigger value)                  │
│ is_star         │ BOOLEAN (true if '*' = always active)             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    extension_commands                                │
├─────────────────────────────────────────────────────────────────────┤
│ id              │ SERIAL PRIMARY KEY                                │
│ extension_id    │ FK → extensions.id                                │
│ command_id      │ VARCHAR (e.g., "extension.helloWorld")            │
│ title           │ VARCHAR (display name in command palette)         │
│ category        │ VARCHAR (optional grouping)                       │
│ icon            │ VARCHAR (optional icon path)                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    extension_contributions                           │
├─────────────────────────────────────────────────────────────────────┤
│ id              │ SERIAL PRIMARY KEY                                │
│ extension_id    │ FK → extensions.id                                │
│ contrib_type    │ VARCHAR (commands, languages, views, etc.)        │
│ contrib_data    │ JSONB (full contribution object)                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    extension_dependencies                            │
├─────────────────────────────────────────────────────────────────────┤
│ id              │ SERIAL PRIMARY KEY                                │
│ extension_id    │ FK → extensions.id                                │
│ dep_type        │ VARCHAR (npm, extension, dev)                     │
│ dep_name        │ VARCHAR (package/extension name)                  │
│ dep_version     │ VARCHAR (version constraint)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Command Detection

**Goal:** Identify every command an extension registers and can execute.

**Data to Collect:**
- Command identifiers (`contributes.commands`)
- Keybindings (`contributes.keybindings`)
- Menu items (`contributes.menus`)
- Context menu entries
- Command palette entries

### 1.3 Activation Event Analysis

**Goal:** Understand when and why an extension activates.

| Event Type | Risk Level | Description |
|------------|------------|-------------|
| `*` | 🔴 High | Always active (potential performance/security impact) |
| `onStartupFinished` | 🟡 Medium | Runs at VS Code startup |
| `onCommand:*` | 🟢 Low | Only on explicit user action |
| `onLanguage:*` | 🟢 Low | When opening specific file types |
| `onUri` | 🟡 Medium | Can be triggered externally |
| `onFileSystem:*` | 🟡 Medium | File access triggers |

### 1.4 Contribution Point Mapping

**Goal:** Map all extension contributions to understand capabilities.

**Contribution Types to Track:**
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

---

## Phase 2: Analysis (Future Sprint)

> ⚠️ **Note:** This phase begins AFTER Phase 1 completion.

### 2.1 Risk Scoring Engine
- Pattern-based risk detection
- Permission analysis
- Behavioral classification

### 2.2 Code Analysis
- JavaScript/TypeScript static analysis
- API call detection
- Network request patterns
- File system access patterns

### 2.3 Comparison & Diff
- Version comparison
- Change detection
- Regression identification

---

## Implementation Tasks

### Database Tasks
- [ ] Create `extension_activation_events` table
- [ ] Create `extension_commands` table
- [ ] Create `extension_contributions` table
- [ ] Create `extension_dependencies` table
- [ ] Generate Alembic migrations
- [ ] Update SQLAlchemy models

### Parser Tasks
- [ ] Create `manifest_parser.py` - Full package.json parsing
- [ ] Create `activation_parser.py` - Activation event extraction
- [ ] Create `command_parser.py` - Command detection
- [ ] Create `contribution_parser.py` - Contribution point mapping
- [ ] Create `dependency_parser.py` - Dependency analysis

### Service Tasks
- [ ] Update `service.py` with new parsers
- [ ] Create CRUD functions for new tables
- [ ] Add API endpoints for querying parsed data

### Schema Tasks
- [ ] Create Pydantic schemas for new data structures
- [ ] Add response models for API endpoints

---

## Priority Order

```
1. extension_commands        ← First (most security-relevant)
2. extension_activation_events  ← Second (trigger analysis)
3. extension_contributions   ← Third (capability mapping)
4. extension_dependencies    ← Fourth (supply chain)
```

---

## Success Criteria

Phase 1 is complete when:
- ✅ All new database tables created and migrated
- ✅ Parsers extract all specified data from package.json
- ✅ API endpoints expose parsed data
- ✅ Test coverage for all parsers
- ✅ Sample extensions fully parsed and stored
