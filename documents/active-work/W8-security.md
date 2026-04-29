# W8 — Security Hardening (Active Work Tracker)

`Last Updated: 2026-04-29`

This is the canonical active work tracker for the W8 security hardening
window. Items have stable IDs (`W8-1` … `W8-8`). Code comments, tests, and
ADR addenda reference items by ID — **keep IDs stable** when reorganizing.

This file was extracted from `REFACTOR_OPTIMIZATION.md §11.5` on
`2026-04-29`. Slim canonical `REFACTOR_OPTIMIZATION.md` no longer carries
the W8-1..W8-8 detail; full historical snapshot at
`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`.

## Status (Quick Glance)

- **W8-1** — landed `2026-04-27` (`MAX_UNCOMPRESSED_SIZE` /
  `MAX_COMPRESSION_RATIO` / `MAX_FILE_COUNT` guards in
  `workflows/marketplace/client.py::_extract_vsix_to_dir`;
  `VSIXUnpackError`; `tests/workflows/marketplace/test_vsix_hardening.py`
  5 cases)
- **W8-2** — landed `2026-04-27` (`feat/w8-2-and-reviewer-feedback-gaps`)
- **W8-3** — landed `2026-04-28` (`feat/w8-3-uri-trigger-argv-form`)
- **W8-4** — landed `2026-04-29` (`executor/binary_paths.py` constants
  - lazy `docker_path()` resolver; `host.py` 6 invocation sites switched
  to absolute paths; `XDG_OPEN_PATH` source-of-truth lives in
  `executor/binary_paths.py` but is *mirrored* inline in
  `executor/flows/playwright/uri_validation.py:27` because that module
  runs inside the executor container as a path-based script — `from
  executor.binary_paths import …` is not resolvable at runtime; sync is
  guarded by `tests/executor/test_absolute_paths.py::test_uri_validation_re_exports_xdg_open_constant`
  (any drift between the two literals fails CI);
  `tests/executor/test_absolute_paths.py` (13 cases) +
  `tests/architecture/test_absolute_binary_paths.py` AST gate (10 self-test
  cases). Out-of-scope `editor.py`/`monitor_runtime.py`/`reset_state.py`/
  `runtime_capture/extension_host.py` carry `# arch-allow: bare-binary-path`
  pragmas pending `[FOLLOWUP w8-4-broader-executor]`.)
- **W8-5** — landed `2026-04-29` (`appcore/contracts/validators.py`
  `valid_extension_slug` + `ACTIVATION_REPORT_NAME_RE` re-import the
  W8-2 `MARKETPLACE_SLUG_TOKEN_RE` constant; router `/{name}` and
  `/{name}/bundle` endpoints gated by FastAPI `Path(..., pattern=...)`;
  duplicate ad-hoc validation removed from
  `workflows/activation_reports/router.py:217-271`;
  `tests/platform/contracts/test_validators.py` (35 cases) +
  `tests/workflows/activation_reports/test_router_path_traversal.py`
  (18 parametrized cases) +
  `tests/architecture/test_extension_slug_regex_drift.py` AST drift gate.
  Status code change: traversal/non-matching paths now 422 instead of 400.)
- **W8-6** — landed `2026-04-29` (`packages/analysis_contracts/evidence.py`
  introduces `ContentSample` Pydantic v2 model with `validate_assignment=True`
  - `redact_secrets` idempotent filter covering 5 secret classes — `aws`
  (env-var + AKIA/ASIA body), `bearer` (Authorization header + bare token),
  `private_key` (BEGIN/END block), `api_key` (≥12-char body envelope), `db_url`
  (postgres/mysql/mongodb/redis user:pass@host); `tests/platform/security/test_content_sample_redaction.py`
  (18 cases — 6 secret-class parametrize + multi-secret + idempotence + 5
  legitimate-text pass-through + empty/None + reassignment + extra-field reject
  - public re-export); `Makefile` `test-security` target extended with
  `tests/platform/security` (partial close on
  `[FOLLOWUP make-test-security-lane-composition]`); ADR 0003 §6.1 redaction
  policy addendum. Out-of-scope: `EvidenceEvent.raw_context` consumer migration
  (`packages/analysis_engine/rules/_common.py` readers stay on dict access until
  W8 closure pass).)
- **W8-7, W8-8** — pending W8 implementation

## Goal

İki review'in kesiştiği **altı güvenlik kritik bulgusu** + iki ek post-PoC
bulgu kapatılır. Stakeholder demo'su için en azından bu tur gerekli —
current state'te scanner'ın kendisi zip-bomb / path-traversal /
command-injection vektörleri içeriyor.

## Scope

1. **W8-1 — VSIX zip-bomb + entry-traversal guard.** *(LANDED 2026-04-27)*
   [`workflows/marketplace/client.py:144`](../../workflows/marketplace/client.py)
   `_extract_vsix_to_dir()` her üye için path-traversal kontrolü
   (`..` reject + `resolve().relative_to(destination_dir)`) yapıyor
   ama compression ratio / maksimum uncompressed size / dosya sayısı
   limiti yok. Malicious VSIX `zipfile.ZipFile(io.BytesIO(...))`
   üzerinden diske doyurabilir (zip-bomb) ya da extraction sırasında
   OOM yaratabilir.
   - **Change:** Module-level sabitler
     `MAX_UNCOMPRESSED_SIZE = 256 * 1024 * 1024`,
     `MAX_COMPRESSION_RATIO = 100`, `MAX_FILE_COUNT = 2_000`;
     `_extract_vsix_to_dir` içinde iteration sırasında
     `cumulative_uncompressed` ve `cumulative_compressed` takip
     edilir, ratio ve toplam size aşımında yeni
     `VSIXUnpackError`'a düşer; path-traversal guard korunur.
   - **Test:** `tests/workflows/marketplace/test_vsix_hardening.py`
     — 5 cases: normal vsix passes, oversize rejects,
     high-compression-ratio rejects, file-count rejects,
     path-traversal still blocked.
   - **Refs:** `workflows/marketplace/client.py:144-170`
     (`_extract_vsix_to_dir` flow); new exception in same module
     or shared util; new test.
   - **Claude:** §1 "Security findings"; **Codex:** §1
     "Supply-chain hardening".

2. **W8-2 — Safe marketplace identity helper.** *(LANDED 2026-04-27)*
   [`workflows/marketplace/client.py:94-103`](../../workflows/marketplace/client.py)
   `get_vsix_path` / `_artifact_name` / `_extension_dir` raw
   publisher/name/version string'lerini filesystem path'e gömüyor;
   adversarial publisher `../../etc` path-injection vector'ü.
   - **Change:** Yeni `workflows/marketplace/identity.py` modülü;
     `safe_marketplace_slug(publisher, name, version) -> str`
     helper'ı regex `^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$` enforcement
     uygular ve `publisher.name-version` canonical format üretir;
     üç call site helper'a taşınır; architecture test
     `raw concat ≠ helper` ihlali bloke eder.
   - **Test:** `tests/workflows/marketplace/test_identity.py` — happy
     path + 5 adversarial input (path traversal, absolute path, null
     byte, unicode confusable, overlength).
   - **Refs:** `workflows/marketplace/client.py:94-103`; new
     `workflows/marketplace/identity.py`; new test; architecture
     test extension.
   - **Claude:** §1 "Path-traversal in identity concat"; **Codex:**
     §1 "Marketplace identity".
   - **Landed:** `packages/marketplace_identity/` + `safe_marketplace_slug`
     helper live (`feat/w8-2-and-reviewer-feedback-gaps`); raw concat
     architecture test
     `tests/architecture/test_marketplace_identity_concat.py` bloke
     ediyor. Plan'daki `workflows/marketplace/identity.py` path'i
     architecture test (`executor/` ↛ `workflows/`) kuralı nedeniyle
     `packages/marketplace_identity/` altına yerleşti — W8-5 import bu
     path'ten yapılır.

3. **W8-3 — URI trigger shell-safe invocation.** *(LANDED 2026-04-28)*
   [`executor/flows/playwright/entrypoint_triggers.py:142`](../../executor/flows/playwright/entrypoint_triggers.py)
   ve
   [`executor/flows/playwright/stimulus_attempts.py:136`](../../executor/flows/playwright/stimulus_attempts.py)
   `xdg-open '{uri}'` şeklinde terminal stimulus üzerinden string
   interpolation yapıyor; trigger payload'ı adversarial olursa
   `'; rm -rf /;'` → terminal command injection vektörü.
   - **Execution context:** İki dosya executor container içinde
     (`docker exec python3 /home/executor/flows/playwright/entrypoint.py`
     ile invoke edilir) çalışır; argv-form `subprocess.run` da container
     içinde execute olur — host shell'ine kaçış yoktur, blast radius
     sandbox'la sınırlıdır. Değişikliğin amacı container içi
     `rm -rf /home/executor` tipi yıkıcı payload'ı kesmek.
   - **Change:** Terminal stimulus yerine
     `subprocess.run(["xdg-open", uri], check=False, timeout=5)`
     argv form; URI validation
     `urllib.parse.urlparse(uri).scheme in {"vscode", "vscode-insiders", "http", "https"}`;
     direct shell string uygulaması iki dosyadan kaldırılır.
   - **Test:** `tests/executor/security/test_uri_trigger_injection.py`
     — `;` / `$(...)` / backtick / pipe içeren payload reddedilir.
   - **Refs:** iki stimulus dosyası + new test.
   - **Claude:** §18 "Shell injection in triggers"; **Codex:** §1.
   - **Landed:** `executor/flows/playwright/uri_validation.py` URI trigger
     argv-form helper live (`feat/w8-3-uri-trigger-argv-form`);
     `subprocess.run` argv form + scheme allow-list (`vscode`,
     `vscode-insiders`, `http`, `https`); shell-template architecture
     test `tests/architecture/test_uri_trigger_shell_pattern.py` bloke
     ediyor; 26 adversarial test case
     `tests/executor/security/test_uri_trigger_injection.py` altında
     pin'li. Plan'daki `stimulus_attempts.py:136` satır referansı `:324`
     olarak güncellendi (line drift).

4. **W8-4 — Absolute binary paths (executor shell invocations).** PATH
   hijacking koruması. W7-landed
   [`executor/container/launch_vscode.sh`](../../executor/container/launch_vscode.sh)
   zaten explicit path disiplini takip ediyor; aynı disiplin
   `entrypoint_triggers.py`, `stimulus_attempts.py`,
   [`executor/host.py::install_extension_in_executor`](../../executor/host.py)
   içinde uygulanır.
   - **Change:** `code` → `/usr/bin/code`, `xdg-open` →
     `/usr/bin/xdg-open` gibi absolute path'ler; fallback resolver
     `shutil.which` test başlangıcında tek seferlik.
   - **Test:** `tests/executor/test_absolute_paths.py` — subprocess
     invocation PATH'siz env ile smoke.
   - **Refs:** iki stimulus dosyası + `executor/host.py`.
   - **Claude:** §18; **Codex:** —.

5. **W8-5 — Activation-report router regex konsolidasyonu
   (defense-in-depth).**
   [`workflows/activation_reports/router.py`](../../workflows/activation_reports/router.py)
   bundle endpoint'i mevcut durumda `..`, `/`, `\\` karakter
   rejection'ı yapıyor (Claude review §3 step 12 "clean" olarak
   işaretlemiş; concrete exploit path yok). Bu madde bir gap
   kapatmıyor; W8-2'nin `safe_marketplace_slug` helper'ı ile tek
   regex disiplinine konsolidasyon — iki farklı validation path'i
   (router-level ad-hoc + marketplace identity) tek source-of-truth
   altında birleşir, drift riski kapanır.
   - **Change:** FastAPI
     `Path(..., regex=r"^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$")` tight
     constraint; validator helper
     `appcore/contracts/validators.py::valid_extension_slug` merkezi
     hale getirilir (yeni W8-2 `safe_marketplace_slug` ile aynı
     regex disiplini paylaşır). **W8-5 regex'i kendi başına
     tanımlamaz** — W8-2'de pinlenen
     `packages.marketplace_identity.MARKETPLACE_SLUG_TOKEN_RE`
     constant'ını re-import eder; böylece iki helper drift edemez.
     Pydantic v2 `@field_validator` wrapper'ı `valid_extension_slug`
     fonksiyonunu üretir; FastAPI `Path(..., regex=...)` aynı
     constant'ı `.pattern` üzerinden kullanır.
   - **Test:**
     `tests/workflows/activation_reports/test_router_path_traversal.py`
     — 6 adversarial path case.
   - **Refs:** `workflows/activation_reports/router.py`; new
     `appcore/contracts/validators.py` (or consolidation); new test.
   - **Claude:** §1; **Codex:** —.

6. **W8-6 — Content-sample secret redaction.** *(LANDED 2026-04-29)*
   `ContentSample` evidence
   artifact'ları rule match'lerinde `.value` olarak embedded
   ediliyor; regex hit'inden bazı satırlar (`.env` satırları gibi)
   raw text olarak rapor'a yazılabilir → rapor diske yazıldığında
   secret disclosure.
   - **Change:** W8'de yeni `packages/analysis_contracts/evidence.py`
     modülü oluşturulur (bugün `ContentSample` adında ayrı bir sınıf
     yok; `contracts.py` içindeki `EvidenceEvent` + rule-match
     payload'ları raw string taşıyor). Yeni `ContentSample.value`
     setter'ı redaction filter'ından geçirilir;
     `AWS_SECRET_ACCESS_KEY=...`, `bearer <token>`,
     `Authorization: Bearer`, private-key header pattern'leri
     `[REDACTED:<class>]` ile değiştirilir; redaction policy
     **ADR 0003 §6** ek maddesi olarak yazılır.
   - **Test:** `tests/platform/security/test_content_sample_redaction.py`
     — 5 secret class (aws, bearer, private-key, generic api-key, db-url).
   - **Refs:** new `packages/analysis_contracts/evidence.py`;
     migration hook'larıyla `EvidenceEvent.context` raw string
     tüketicileri W8 sonuna kadar yeni API'ya geçer; ADR 0003
     update; new test.
   - **Claude:** §1; **Codex:** §1.

7. **W8-7 — Local network binding discipline (ADR 0007).** Today
   `.env.example` ships `API_HOST=0.0.0.0`, `API_CORS_ALLOW_ORIGINS=*`,
   and `docker-compose.yml` maps the API, UI, executor noVNC + CDP
   ports, and PostgreSQL on every host interface
   (`docker-compose.yml:11-12,27-28,66-68,101-102,119-120` —
   none of the host port mappings carry a `127.0.0.1:` prefix). The
   single-operator trust model from ADR 0001 §1 / ADR 0002 §5 is left
   as a comment in `.env.example:82-84` ("INTERNAL USE ONLY ... ensure
   it runs in a trusted network") with no enforcement. A LAN-adjacent
   attacker today reaches CDP `9222` unauthenticated and can drive the
   live VS Code instance.
   - **Change:** Per ADR 0007, every host-facing port defaults to
     `127.0.0.1`; compose `ports:` entries gain explicit
     `127.0.0.1:` prefixes; `appcore/api/config.py::APISettings.HOST`
     defaults to `127.0.0.1` and `CORS_ALLOW_ORIGINS` defaults to
     `["http://localhost:3000"]`; LAN exposure is opt-in through a
     single `EXTRACE_ALLOW_LAN=1` env var that the entrypoints inspect;
     the executor CDP port mapping moves behind a Compose `debug`
     profile so it is absent from `docker compose up` by default.
     `.env.example` security notice rewritten to describe the
     loopback default + opt-in path.
   - **Test:** new `tests/architecture/test_default_bindings.py` —
     loads `appcore/api/config.py` settings with empty env, asserts
     `settings.api.HOST == "127.0.0.1"` and
     `settings.api.CORS_ALLOW_ORIGINS != ["*"]`; parses
     `docker-compose.yml` and asserts every default-profile `ports:`
     entry begins with `127.0.0.1:` (or is gated behind a non-default
     profile). Companion runbook
     `documents/runbooks/lan-exposure.md` carries the operator-side
     hardening checklist (firewall rules, reverse-proxy auth, CORS
     allow-list, rotated PostgreSQL password) that must precede the
     `EXTRACE_ALLOW_LAN=1` flip.
   - **Refs:** new
     [`documents/adrs/0007-local-network-binding.md`](../adrs/0007-local-network-binding.md);
     `.env.example`; `docker-compose.yml`; `appcore/api/config.py`;
     `Makefile` (dev targets); root `README.md` "Service Endpoints"
     section; new test + new runbook.
   - **Supplementary review:** 2026-04-25 (Codex review surfaced the
     ingress side of the trust boundary; original Claude/Codex W8
     review covered scanner-side parsing/injection only).

8. **W8-8 — Manifest field log-injection sanitization (defense-in-depth).**
   Adversarial extension manifests carry attacker-controlled strings
   in `displayName`, `publisher.displayName`, `description`,
   `repository.url`, ve `categories[]`. Bu alanlar marketplace
   ingestion + extension-catalog lifecycle üzerinden geçip logger
   emit + job snapshot persist path'ine ulaşıyor. Merkezi bir
   sanitization pass'i yok: kötü niyetli bir publisher kendi
   `displayName`'ine `\n` / `\r` / ANSI control sequence gömerek
   (a) post-W13-4 `extrace.executor.*` log akışında satır forge
   edebilir, (b) `output/*.json` artifact'ını terminalde inceleyen
   operatörü ANSI escape ile kandırabilir.
   - **Change:** Yeni
     `appcore/contracts/sanitize.py::sanitize_for_log(value, *, max_length=200)`
     helper'ı CR/LF + C0/C1 control character'larını `\x{HH}` formuna
     escape eder, NULL byte'ı reddeder, max_length aşımında
     `…` ile keser. Helper, manifest field'ları log emit eden tüm
     call site'larda
     `logger.info("event %s", sanitize_for_log(displayName))` formuna
     geçer. Job snapshot persist'i (`crud_ops/analysis_jobs.py`)
     raw manifest field'ı saklamaya devam eder (DB integrity); log /
     evidence path'inde sanitize edilmiş varyant kullanılır. ADR 0002
     §7'ye "untrusted manifest → log forging" satırı eklenir.
   - **Test:**
     `tests/platform/security/test_manifest_log_sanitization.py` —
     6 case: newline injection, CR injection, ANSI escape, NULL byte
     reject, overlength truncation, ve regression: legitimate unicode
     `displayName` ('日本語', 'müzik') preserved (UTF-8 encode
     pass-through).
   - **Refs:** new `appcore/contracts/sanitize.py`;
     `workflows/extension_catalog/service.py` (manifest log emit);
     `workflows/marketplace/job_service.py` (job log emit);
     `workflows/marketplace/analysis_execution.py` (step log emit);
     ADR 0002 update; new test.
   - **Architecture audit (2026-04-27):** §7 "Untrusted input →
     logging" gap "Bilinmiyor" olarak bırakılmıştı; bu madde her
     emit site'ında audit yerine emit-time enforcement ile boşluğu
     kapatır.

## Non-Goals

- Container egress allowlist (W13 observability ayağına bağlı —
  egress logları run-ID ile stamp'lenmeden allowlist audit'i
  anlamlı değil).
- Harness extension sandbox (W4 ExecutorControl bar'ı kapattı).
- T2/T3 fixture lane (POST_POC_BACKLOG).
- Rotated production PostgreSQL credentials (operator responsibility
  per ADR 0007 §5; the ADR rewrites the `.env.example` notice but does
  not auto-rotate).

## Entry

§11.1 entry gate green (`REFACTOR_OPTIMIZATION.md` slim canonical).

## Exit

- [ ] 8 yeni security test lane green
- [ ] `make test-security` 41 → ≥49 passing
- [x] ADR 0003 §6.1 redaction policy addendum merged (LANDED 2026-04-29 on
      `feat/w8-6-content-sample-redaction`).
- [ ] ADR 0002 §7 "untrusted manifest → log forging" addendum merged
- [ ] `appcore/contracts/sanitize.py::sanitize_for_log` live; manifest
      field log emit site'ları (extension_catalog, marketplace
      job_service + analysis_execution) helper'a geçirilmiş;
      `tests/platform/security/test_manifest_log_sanitization.py`
      green
- [ ] Container-packaging ADR (number TBD; ADR 0008 if next available)
      **draft** başlamış
      (merged olması gerekmiyor — W9 girişinde merged olur)
- [ ] ADR 0007 (local network binding) merged; `.env.example` +
      `docker-compose.yml` + `appcore/api/config.py` defaultları
      `127.0.0.1` / allow-list CORS; `EXTRACE_ALLOW_LAN=1` opt-in
      yolu doğrulanmış; `documents/runbooks/lan-exposure.md` live
- [x] `packages/marketplace_identity/` + `safe_marketplace_slug` helper
      live (LANDED 2026-04-27 on `feat/w8-2-and-reviewer-feedback-gaps`);
      raw concat architecture test
      `tests/architecture/test_marketplace_identity_concat.py` bloke
      ediyor.
- [x] `executor/flows/playwright/uri_validation.py` URI trigger argv-form
      helper live (LANDED 2026-04-28 on `feat/w8-3-uri-trigger-argv-form`);
      `subprocess.run` argv form + scheme allow-list (`vscode`,
      `vscode-insiders`, `http`, `https`); shell-template architecture
      test `tests/architecture/test_uri_trigger_shell_pattern.py` bloke
      ediyor; 26 adversarial test case
      `tests/executor/security/test_uri_trigger_injection.py` altında
      pin'li.
- [x] `executor/binary_paths.py` constants + `docker_path()` resolver live
      (LANDED 2026-04-29); `host.py` 6 invocation sites use absolute paths;
      `XDG_OPEN_PATH` source-of-truth in `binary_paths.py`, *mirrored*
      inline in `executor/flows/playwright/uri_validation.py:27` because
      that module runs as a path-based script in the executor container
      (cross-package imports unresolvable at runtime); drift guarded by
      `tests/executor/test_absolute_paths.py::test_uri_validation_re_exports_xdg_open_constant`.
      AST gate `tests/architecture/test_absolute_binary_paths.py` blocks
      bare-name literals in `executor/`. Out-of-scope sites carry
      `# arch-allow: bare-binary-path` pragmas pending
      `[FOLLOWUP w8-4-broader-executor]`.
- [x] `appcore/contracts/validators.py` `valid_extension_slug` +
      `ACTIVATION_REPORT_NAME_RE` live (LANDED 2026-04-29); activation-report
      router `/{name}` and `/{name}/bundle` endpoints use FastAPI
      `Path(..., pattern=...)` gate; AST drift gate
      `tests/architecture/test_extension_slug_regex_drift.py` blocks
      duplicate slug regex literals; status code shift 400 → 422 documented.
- [x] `packages/analysis_contracts/evidence.py` `ContentSample` Pydantic v2
      model + `redact_secrets` 5-class filter live (LANDED 2026-04-29 on
      `feat/w8-6-content-sample-redaction`); 18-case
      `tests/platform/security/test_content_sample_redaction.py` pinned;
      `Makefile` `test-security` target extended with `tests/platform/security`
      (partial close on `[FOLLOWUP make-test-security-lane-composition]`,
      W8-1/W8-3/W8-8 lane membership still deferred to W8 closure).
- [ ] `tests/architecture/test_default_bindings.py` green
      (varsayılan settings `0.0.0.0` üretmiyor; compose `ports:`
      entries `127.0.0.1:` prefix'li veya `debug` profile altında)
