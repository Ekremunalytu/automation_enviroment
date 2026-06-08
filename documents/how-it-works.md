# How ExTrace Works

ExTrace is a sandboxed analysis system for suspicious VS Code extensions. It
combines static checks, controlled runtime execution, and report review so an
analyst can decide whether an extension deserves deeper investigation.

It is not a public malware scanning service. The intended deployment is a
single analyst running a local or lab appliance.

## The Basic Workflow

```text
Extension folder or VSIX
        |
        v
Manifest and source extraction
        |
        v
Static pre-check rules
        |
        v
Trigger planning
        |
        v
Sandboxed VS Code runtime
        |
        v
Evidence reports
        |
        v
Analyst review in API or UI
```

## Inputs

ExTrace can work with:

- An extension folder already present on disk.
- A `.vsix` file.
- A Marketplace extension downloaded through the API.
- Synthetic fixtures used by tests.

Real malicious samples must not be committed to this repository. Test fixtures
should be synthetic, declawed, and safe to store.

## Static Analysis

Static analysis looks at the extracted extension tree before any runtime
execution. It can flag behavior such as:

- Reverse shell patterns.
- Download cradles.
- Native `.node` loaders.
- Invisible Unicode or source-hiding runs.
- Credential file reads combined with outbound network sinks.
- Cross-extension tampering.
- Path traversal in local servers.
- Stylesheet-based execution or exfiltration.
- RMM-as-RAT configuration patterns.

Static rules live under `static_runtime/rules/`. Static findings can warn or
block before the extension reaches the runtime sandbox.

## Runtime Analysis

Runtime analysis launches VS Code in a container and drives it with Playwright.
The executor can attempt extension activation, contributed command execution,
UI interactions, and scenario-specific stimuli. It records what happened and
how trustworthy the run was.

Important runtime outputs include:

- Activation events observed.
- Evidence events linked to the target extension when attribution is possible.
- Attempted stimuli.
- Verification gaps.
- Health signals, including crashes and incomplete runs.

Runtime evidence is strongest when a behavior is both attempted and verified.
An attempted command by itself is not proof that the extension behavior was
successfully observed.

## Reports

Reports are written under `output/` and exposed through the API and UI. The
important distinction is:

- **Static report**: what the source tree and manifest suggested.
- **Activation report**: what the runtime harness observed.
- **Job metadata**: whether the analysis job started, ran, failed, completed,
  or was cancelled.
- **Health and quality fields**: whether the run should be trusted as complete.

The UI presents these as analyst-facing evidence, not as a binary "safe" or
"malware" label.

## Major Components

| Component | Purpose |
|---|---|
| `appcore/` | Shared platform code: settings, DB, storage, contracts |
| `workflows/` | Backend workflows for catalog, reports, marketplace, and jobs |
| `executor/` | Dockerized VS Code runtime and Playwright automation |
| `static_runtime/` | Static pre-check rules and static analyzer entry points |
| `packages/` | Framework-agnostic contracts and analysis logic |
| `ui/` | React analyst console |
| `documents/` | Source-of-truth architecture, ADR, roadmap, agent docs, and human-readable guides |
| `deploy/podman/` | Air-gapped Podman deployment bundle |

## Security Boundaries

The design assumes extension input is adversarial.

- The API, UI, executor, static analyzer, and database run as separate
  services.
- Runtime execution is isolated in Docker or Podman containers.
- The static analyzer is network-isolated.
- Default service bindings are loopback-only.
- LAN exposure is an operator decision and must follow the LAN runbook.
- Database writes go through the storage layer, with Pydantic validation before
  insertion.

The full hard rules are in [../AGENTS.md](../AGENTS.md).

## Known Limits

ExTrace does not guarantee complete malware detection.

Known limits include:

- Platform blind spots when a sample only detonates on another OS.
- Dynamic blind spots when a command is attempted but cannot be verified.
- Environment-aware samples that detect sandbox timing, filesystem, or UI
  differences.
- Static approximations that catch behavior classes but do not prove intent.
- Single-operator assumptions: it is not hardened as a public multi-tenant
  service.

Those limits are intentional and should be visible in reports, risks, and ADRs.
