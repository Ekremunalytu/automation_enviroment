# W15 — Codex U-class Close-Out + UI Bounds + Posture (Active Work Tracker)

`Last Updated: 2026-05-17 (W15 active; week15 cut from main HEAD 7cc2921 on 2026-05-14; W15-1 closed via c58c365 — sync analyze error taxonomy parity, M10; W15-2 closed via 765cde7 — clean_workspace is_symlink-before-rmtree, M12; W15-3 closed via 3512a7c — activationEvents bounds + Alembic field-length migration, U8; W15-4 closed via 89e13e3 — UI bounds bundle (timeline/density/relations graph caps with truncation indicators), U1/U2/U3 + U6; W15-5 closed 2026-05-17 via 43d6438 — quick fixes bundle: UI /health proxy I2 + lifecycle "for <id>" regex I4; W15-6 closed 2026-05-17 via be52520 — ADR 0011 unauthenticated catalog endpoints posture (Accepted and implemented; Proposed at e41722e); workflows/extension_catalog/router.py module docstring + router construction-site comment cite ADR 0011; new tests/architecture/test_catalog_endpoint_posture.py gate locks three AST invariants (docstring cite + no auth dependency + endpoint-count lock at 12); ADR 0002 NOT amended (Option A); U10/U11 audit row closes; W15-1 post-slate typing hotfix via 976dc96 — ANALYZE_*_ERROR_TYPES annotation BaseException → Exception narrowing (surfaced by W15-4 close-out mypy gate); W15 mid-iter hygiene 2026-05-16 via 878da2c — seven canonical/newcomer-facing doc preambles refreshed to W15 truth-state + doc-preamble consistency arch gate + README phase-pointer test W14 → W15 with W14 close-out merge tracking; W15-7 partial close (compose-image-pin + gh-action-trivy-pin still pending); three new audit findings appended to POST_POC_BACKLOG — health-reconciliation-responsibility-split, marketplace-router-test-suite-split, analysis-job-worker-entry-crud-ownership; W14 close-out PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 week13 -> main MERGED 2026-05-13 via 772deb3)`
`Phase: W15 active (W15-1..W15-6 closed; W15-7 pending)`
`Branch: week15 (cut from main HEAD 7cc2921 on 2026-05-14)`
`Owner: ekrem`

> **Authored 2026-05-14** as the W15 scope skeleton. Stable IDs `W15-1..W15-7`
> are reserved by the iteration plan and **assigned at first pull** per the
> W11/W12/W13/W14 precedent (`REFACTOR_OPTIMIZATION.md` §13.0). Remaining
> sub-iter IDs (`W15-2`..`W15-7`) fill in as each is pulled.

This is the canonical active work tracker for the W15 Codex U-class
Close-Out + UI Bounds + Posture window. Items receive stable IDs (`W15-1`,
`W15-2`, ...) **at first pull**, not preemptively, per the
W11/W12/W13/W14 precedent.

This file mirrors the structure of
[`W14-codex-acceptance-observability.md`](W14-codex-acceptance-observability.md).
Slim canonical [`REFACTOR_OPTIMIZATION.md §13`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and current candidate
list.

## Status (Quick Glance)

+ **W15 active — `week15` branch cut from `main` HEAD `7cc2921` on
  `2026-05-14`.** W15-1 closed `2026-05-14` via `c58c365` (sync analyze
  error taxonomy parity, M10 close); W15-2 closed `2026-05-14` via
  `765cde7` (`clean_workspace` is_symlink-before-rmtree, M12 close);
  W15-3 closed `2026-05-15` via `3512a7c` (activationEvents bounds +
  Alembic field-length migration, U8 close); W15-4 closed `2026-05-16`
  via `89e13e3` (UI bounds bundle: `EventTimeline` / `EventDensityStrip`
  / `InteractionsSection` caps + truncation indicators driven by new
  `ui/src/lib/displayCaps.ts`; U1/U2/U3 + U6 close; 21 new vitest cases
  across 3 files; `+0` arch gates per tracker exit criteria); W15-5
  closed `2026-05-17` via `43d6438` (quick fixes bundle: I2 UI
  `/health` proxy fix via new `appcore/api/health_router.py`
  (`prefix="/api"`) + `ui/src/lib/api/client.ts` `/health` →
  `/api/health` migration with legacy root `/health` preserved for
  external-monitoring back-compat; I4 lifecycle `for <id>` regex
  tightening — two `_LIFECYCLE_MARKER_PATTERNS` entries in
  `executor/flows/playwright/runtime_capture/extension_host_log_parse.py`
  narrowed from `\s*…\.*?(?P<id>[\w.\-]+)` to
  `\s+…(?:\s+for)?\s+(?P<id>[\w-]+\.[\w.\-]+)` enforcing the VS Code
  marketplace `<publisher>.<name>` id shape; +14 behavioral cases
  (3 backend pytest + 2 UI vitest + 9 parser unit parametrize);
  `+0` arch gates per tracker exit criteria — W14-6
  "extend, do not duplicate" check found no existing extendable
  gate for either fix, new gates deferred to W15-7 close-out
  hygiene); W15-6 closed `2026-05-17` via `be52520` (ADR 0011
  Accepted and implemented — Proposed at `e41722e`, Accepted at
  `be52520`; Option A: catalog endpoints remain unauthenticated
  under three preconditions — single-host appliance scope (ADR 0001),
  loopback bind default (ADR 0007 §1), and operator-side hardening
  for LAN exposure per `documents/runbooks/lan-exposure.md`;
  `workflows/extension_catalog/router.py` module docstring + router
  construction-site comment cite ADR 0011 verbatim; new
  `tests/architecture/test_catalog_endpoint_posture.py` gate locks
  three AST invariants — docstring cite, no auth dependency, and
  endpoint-count lock at 12; `tests/architecture/` 188 → 191 passing
  (+1 gate file, +3 test functions); ADR 0002 NOT amended — ADR 0011
  cites §4 row 102 + §5 as load-bearing prerequisites); W15-1
  post-slate typing hotfix landed `2026-05-16` via `976dc96`
  (`ANALYZE_*_ERROR_TYPES` annotation `tuple[type[BaseException], …]`
  → `tuple[type[Exception], …]`, surfaced by W15-4 close-out
  `make typecheck`; W14-7 hotfix precedent); W15-7 pending —
  regression lock-in umbrella (compose image SHA pin + GH action
  trivy version pin + final preamble refresh). **W15 mid-iter
  hygiene `2026-05-16`:** W15-7
  doc-preamble truth-state refresh alt kümesi pull-forward edildi
  (W15-5'in queue'da olduğu noktada eski W14 preamble'ları üzerine
  inşa etmemek için). Yedi canonical / newcomer-facing doc preamble'ı
  W15 truth-state'e refresh edildi (`CLAUDE.md`, `AGENTS.md`,
  `README.md`, `documents/AGENT_CONTEXT.md`,
  `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md`,
  `documents/REFACTOR_OPTIMIZATION.md`); yeni cross-doc consistency
  arch gate `tests/architecture/test_doc_preamble_consistency.py`
  eklendi; mevcut `tests/architecture/test_readme_phase_pointer.py`
  W14'den W15'e taşındı ve W14 close-out merge fact'ini takip eden
  ek bir behavioral case W13-precedent ile simetrik olarak eklendi
  (`tests/architecture/` 186 → 188 passing). Üç yeni audit finding
  `POST_POC_BACKLOG.md`'a eklendi:
  `[FOLLOWUP health-reconciliation-responsibility-split]` (Engineering
  Quality), `[CLEANUP marketplace-router-test-suite-split]`
  (Engineering Quality), ve `[FOLLOWUP analysis-job-worker-entry-crud-ownership]`
  (Workflow / Platform). W15-7 umbrella'sının kalan alt kalemleri
  (`compose-image-mutable-ref-pin` + `gh-action-trivy-version-pin`)
  hâlâ pending — W15-7 finalize'da kapanacak. W14 close-out PR #21
  (`week14 -> main`) **MERGED** `2026-05-14` via `4e03c8d`; all
  W14-1..W14-8 closed. W15 base differs from the scope-skeleton plan
  note (`4e03c8d`) because the `7cc2921` ("docs(W15): scope skeleton
  + …") commit on `main` carries the W15 tracker itself and must be
  in-branch for the lane file to exist; cutting from `4e03c8d` would
  have required re-applying the skeleton on the branch.
+ **Entry gate (met + branch open).** W15-1 pulled:
  + W14 close-out PR #21 ✓ **MERGED** `2026-05-14` via `4e03c8d`
    (close-out PR included W14-1..W14-8 sub-iter ratchet'leri +
    close-out hygiene pass — Ruff lint, UI contract sync, markdown
    formatting, doc truth-state alignment, `make markdownlint` gate,
    ADR code fence arch test).
  + W14 final/post-merge baseline (re-recorded `2026-05-14` at W15-1
    pull on `week15`): `tests/architecture/` **172 passed** (W14 final
    171 + close-out hygiene ADR-code-fence gate = 172; the W14 tracker
    listed 171 because the hygiene gate counted as a separate +1 and
    was added at the close-out PR rather than within the W14-8
    landing). `make test-security` **215 passed** (unchanged from W13
    final). `make test-local` not re-run at pull (requires Docker
    postgres_test; behavioral coverage validated via targeted suites
    — see W15-1 Per-Item Detail for verification scope).
  + Close-out prerequisites recorded; W15-open checklist complete at
    `2026-05-14` branch cut.
+ **Sub-iteration scope (locked, IDs assigned at pull).**

| Iter | Tema | Stable ID(s) | Tahminî efor |
|---|---|---|---|
| **W15-1** ✅ | Sync analyze error taxonomy alignment — closed `2026-05-14` via `c58c365` | `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` | 1 oturum |
| **W15-2** ✅ | Workspace symlink check order / orphan removal — closed `2026-05-14` via `765cde7` | `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` | 1 oturum |
| **W15-3** ✅ | `activationEvents` bounds + DB field-length migration — closed `2026-05-15` via `3512a7c` | `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` | 1 oturum (tek-PR uygulandı) |
| **W15-4** ✅ | UI bounds bundle: timeline + density strip + relations graph caps with truncation indicators — closed `2026-05-16` via `89e13e3` (+ W15-1 typing hotfix `976dc96`) | `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` + `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` | 1 oturum (tek-PR uygulandı) |
| **W15-5** ✅ | Quick fixes bundle: UI `/health` proxy (I2) + lifecycle `for <id>` regex (I4) — closed `2026-05-17` via `43d6438` | `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` + `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` | 1 oturum (tek-PR uygulandı) |
| **W15-6** ✅ | Unauthenticated catalog endpoints posture (ADR 0011) — closed `2026-05-17` via `be52520` (Proposed at `e41722e`) | `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` | 2 oturum (ADR + implementation) |
| **W15-7** | Regression lock-in umbrella: compose image pin + GH action pin + doc preamble refresh | `[FOLLOWUP compose-image-mutable-ref-pin]` + `[FOLLOWUP gh-action-trivy-version-pin]` + (post-W14 audit) doc-preamble truth-state refresh | 1 oturum |

+ **Pull sequence rationale.** W15-1 ve W15-2 önce — düşük blast radius,
  her ikisi de izole tek-dosya/birkaç-dosya fix. Sonra W15-3 (DB migration
  içerdiği için orta-risk; izole bir pull olarak güvenli sequencing
  ister — schema değişiklikleri başka sub-iter'lara karışmamalı). W15-4
  ve W15-5 sonraki adım: UI tarafı odaklı, generated `contracts.ts`'ye
  dokunmaz (UI-side caps + view-model). W15-6 (U10-U11) ADR-pending bir
  posture decision; ADR önce yazılır, sonra kod uygulanır — bu sebeple
  geç çekilir. W15-7 en son: W14-6 pattern'i — regression lock-in
  umbrella ratchet/pin türü kalemler en sonda toplanır.

## Entry Conditions (ticked at W15 open `2026-05-14`)

+ [x] W14 closed and merged to `main` via close-out PR #21 (`4e03c8d`,
  `2026-05-14`); close-out PR included W14-1..W14-8 ratchet bundle +
  close-out hygiene pass.
+ [x] W14 sub-iter slate complete (W14-1..W14-6) + post-slate hotfixes
  (W14-7 container-shipping regression + W14-8 preventive Python 3.11+
  API gate) closed `2026-05-13`.
+ [x] W14 final architecture gate count recorded: `tests/architecture/`
  **172** (W14-8 lifted 170 → 171; close-out hygiene PR ADR code fence
  arch test added the +1 separately counted as 171 → 172 on the
  post-merge baseline; `make markdownlint` is a Make-target gate, not
  a pytest case). Re-recorded at W15-1 pull on `week15`.
+ [x] W14 final/post-merge `make test-security` re-recorded **215
  passed** (unchanged from W13 final). `make test-local` not re-run
  at pull (requires Docker postgres_test); behavioral parity for
  W15-1 validated via targeted suites — full `make test-local`
  baseline re-record deferred to the next sub-iter that exercises
  cross-module behavior (or to the W15 close-out hygiene pass).
+ [x] W15 lane document (this file) header updated to `Phase: W15 active`
  per W11/W12/W13/W14 precedent at the explicit branch cut / first pull
  (`2026-05-14`).

## Goal (per `REFACTOR_OPTIMIZATION.md` §13)

Üç tamamlayıcı thrust:

1. **Codex U-class + I-class acceptance-bar pull-forward (close-out).**
   W14 H-class (W13) + M-class (W14-2 + W14-3) close'larından sonra geriye
   2026-05-10 Codex Cloud audit'inde U-class (U1-U3, U6, U8, U10-U11) +
   I-class (I2, I4) + tail M-class (M10, M12) kaldı. W15 bu kalemleri
   kapatır; sonra Codex 2026-05-10 audit kapanmış olur (verified-closed
   audit trail'e taşınır).

2. **Posture decision.** `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`
   architectural bir karar (ADR pending) — W15-6 bu ADR'ı 0011 olarak
   yazar ve uygular. Karar tek seferlik bir gate; gelecekteki posture
   shift'leri ADR amendment ile yapılır.

3. **Post-W14 close-out audit findings — regression lock-in umbrella.**
   W14 close-out audit (`2026-05-14`) iki açık hijyen kalemi tespit
   etti: (a) `docker-compose.yml`'da mutable image ref'ler
   (`postgres:16-alpine`, `alpine/socat:latest`), (b) `.github/workflows/
   security.yml`'da mutable GH action ref (`aquasecurity/trivy-action@
   master`). Ayrıca audit'in immediate önerisi olarak 4 canonical
   preamble post-merge truth-state refresh. Hepsi W15-7'de bundle olur.

## Candidate Items (stable IDs assigned at first pull)

`Status` reflects current backlog state; `W15-N` IDs fill in as items move
from "not started" to "in progress". Items prefixed
`[FOLLOWUP codex-2026-05-10-…]` rows are from the `2026-05-10` Codex Cloud
audit; `[FOLLOWUP compose-image-mutable-ref-pin]` and
`[FOLLOWUP gh-action-trivy-version-pin]` are from
[`POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md) Engineering Quality.

| ID | Item | Lane | Status |
|---|---|---|---|
| **W15-1** | `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` (sync `/api/marketplace/analyze` entry, async path ile error taxonomy uyumsuz — async tarafı pydantic ValidationError + 4xx döner, sync tarafı generic Exception'a düşüp 500 emit ediyor; aynı request shape iki farklı status alıyor) | `[platform-storage]` `[security-detection]` | **closed `2026-05-14` via `c58c365`** |
| **W15-2** | `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` (`clean_workspace()` orphan symlink handling — check sırası TOCTOU window'u açıyor; ya kontrol sırası fix edilir ya da dead code olarak silinir; W14 audit'inde dokunulmadı) | `[executor-runtime]` `[security-detection]` | **closed `2026-05-14` via `765cde7`** (path b: fix — `clean_workspace` mevcut `_clear_directory` desenine hizalandı; live caller `reset_state.py:176`'da olduğu için dead-code removal yolu açık değildi) |
| **W15-3** | `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` (`activationEvents` liste/string boyutu unbounded; oversized manifest DoS + DB row inflation; cap + Alembic field-length migration ister) | `[security-detection]` `[platform-storage]` | **closed `2026-05-15` via `3512a7c`** (Pydantic schema + manifest_parser defense-in-depth + DB column shrink + Alembic migration; +6 arch gates + 8 behavioral cases) |
| **W15-4** | `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` (UI event density / timeline spread / count operations unbounded; large activation report → UI freeze) | `[ui]` | **closed `2026-05-16` via `89e13e3`** (`EventTimeline` + extracted `EventDensityStrip` apply `applyDisplayCap` post-filter at `DISPLAY_CAPS.TIMELINE_EVENTS=800` / `EVENT_DENSITY_EVENTS=800`; truncation indicators emit `+N more · showing first 800 of M events · filter to narrow` and `+N events truncated · density reflects first 800 of M`) |
| **W15-4** | `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` (relations graph node-edge count unbounded; large extension reports UI graph render'ı yavaşlatıyor) | `[ui]` | **closed `2026-05-16` via `89e13e3`** (`InteractionsSection` adds `+N groups not shown` Eyebrow in `Panel right` slot when `graph.groups.length` exceeds `DISPLAY_CAPS.RELATIONS_GROUPS=5`; `InteractionGraph` literal `5` and `LEAF_CAP=6` swapped for value-preserving `DISPLAY_CAPS.RELATIONS_GROUPS` / `DISPLAY_CAPS.RELATIONS_LEAVES_PER_GROUP` imports — existing `+${overflow} more` leaf indicator untouched) |
| **W15-5** | `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` (UI client `/health` fetch'i nginx `/api/*` proxy'sini bypass ediyor olabilir; reverse-proxy posture'a uyumsuz; verify + fix) | `[ui]` `[platform-storage]` | **closed `2026-05-17` via `43d6438`** (additive backend `/api/health` route via new `appcore/api/health_router.py` mounted with `prefix="/api"`; UI `apiClient.getHealth` migrated `/health` → `/api/health`; legacy root `/health` preserved for external-monitoring back-compat) |
| **W15-5** | `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` (lifecycle `"for <id>"` regex çok geniş; daraltma — log-noise + false-positive parser drift'i) | `[executor-runtime]` | **closed `2026-05-17` via `43d6438`** (two `_LIFECYCLE_MARKER_PATTERNS` entries in `extension_host_log_parse.py` tightened — `\s*…\.*?` → `\s+…(?:\s+for)?\s+` anchor; id capture `[\w.\-]+` → `[\w-]+\.[\w.\-]+` enforcing `<publisher>.<name>` VS Code marketplace id shape; narrow `(<id>)` parenthesis form + register patterns preserved untouched) |
| **W15-6** | `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` (auth posture decision; ADR 0011 — single-host appliance scope altında catalog endpoint'leri auth'suz mu, marker-based mı? Karar ADR ile, sonra koda uygulanır) | `[platform-storage]` `[security-detection]` | **closed `2026-05-17` via `be52520`** (Option A — remain unauthenticated; ADR 0011 Accepted and implemented; Proposed at `e41722e`; `workflows/extension_catalog/router.py` module docstring + router construction-site comment cite ADR 0011; new `tests/architecture/test_catalog_endpoint_posture.py` with three AST invariants (docstring cite + no auth dependency + endpoint-count lock at 12); ADR 0002 NOT amended) |
| **W15-7** | `[FOLLOWUP compose-image-mutable-ref-pin]` (`docker-compose.yml` `postgres:16-alpine` + `alpine/socat:latest` mutable tag'ler; SHA digest pin'e geç; `test_dockerfile_digest_pin.py`'ı compose `image:` anahtarlarını kapsayacak şekilde **extend**) | `[platform-storage]` | not started |
| **W15-7** | `[FOLLOWUP gh-action-trivy-version-pin]` (`.github/workflows/security.yml` `aquasecurity/trivy-action@master` mutable ref; version pin) | `[platform-storage]` | not started |
| **W15-7** | (post-W14 close-out audit immediate finding) doc preamble truth-state refresh — `CLAUDE.md`, `AGENTS.md`, `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md`, `documents/AGENT_CONTEXT.md`, `documents/REFACTOR_OPTIMIZATION.md`, `README.md` "close-out PR week14 -> main next" cümleleri W14 merge'den sonra refresh edilmedi (refresh PR #21'in close-out hygiene commit'inde kısmen yapıldı; W15 close-out hygiene'da finalize) | `[docs-maintenance]` | **mid-iter partial close `2026-05-16` via `878da2c`** — yedi canonical/newcomer-facing doc preamble refresh + cross-doc consistency arch gate (`test_doc_preamble_consistency.py`) + README phase-pointer test W14 → W15 + W14 close-out merge tracking case; compose-image-mutable-ref-pin + gh-action-trivy-version-pin alt kalemleri hâlâ pending (W15-7 finalize) |
| TBD watch | `[FOLLOWUP install-extension-cold-start-ipc-hang]` (W14-7 doğrulama sırasında ortaya çıkan VS Code IPC ack timeout; W14-7 fix'i bu yola dokunmadı; W15+ aday — direct trigger yok) | `[executor-runtime]` | watching — defer |

## Sub-iteration Scope Locks

Aşağıdaki bloklar her iterasyonun **scope kilit dokümantasyonudur**. İlk
pull'da sub-iterasyonun başlığı `W15-N — …` olarak finalize edilir ve
"Per-Item Detail" bölümüne taşınır.

### W15-1 scope — Sync analyze error taxonomy alignment

**Pull source.** [POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md) "Codex Cloud
Audit Backlog → Post-W13 Candidates" → `[FOLLOWUP codex-2026-05-10-M10-
sync-analyze-typeerror-catch]`.

**Hedef.** Sync `/api/marketplace/analyze` entry'sinin error catch'i async
path ile aynı taxonomy'i kullansın. Async tarafı (job-driven path)
pydantic `ValidationError` → 4xx, `ExtensionNotFoundError` → 4xx,
geri kalan `Exception` → 5xx döner. Sync entry generic `try/except` ile
tüm hataları 500'e çeviriyor (M10'un Codex audit notu); aynı request
şekli iki farklı status code alıyor.

**Etkilenen yollar.**

+ [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py)
  (384 LoC; sync entry + async path)
+ [workflows/marketplace/router.py](../../workflows/marketplace/router.py)
  — sync vs async endpoint'lerin error handler'ları
+ Olası: ortak error-taxonomy helper'ı (yeni veya mevcut — analysis_service
  içinde küçük helper yeterli)

**Adımlar.**

1. Async tarafın error taxonomy'sini çıkar (hangi exception → hangi
   status code → hangi response body).
2. Sync entry'yi aynı taxonomy'ye hizala; generic Exception catch
   yerine specific exception classes + ortak helper.
3. Yeni architecture gate `tests/architecture/test_analyze_error_
   taxonomy_parity.py` — AST'de sync ve async entry'lerin aynı
   exception sınıflarını handle ettiğini ve aynı status code map'ini
   kullandığını assert.
4. Behavioral regression: `tests/workflows/marketplace/test_analyze_
   error_taxonomy.py` (yeni) — her exception sınıfı için sync ve async
   parametrize.

**Test paterni.** Architecture gate (AST parity) + behavioral
parametrize (W14-2'nin `_coerce_safe_epoch_s` deseni gibi: input × beklenen
status × beklenen body).

**Exit kriterleri.**

+ 1 yeni architecture gate (`tests/architecture/` 171 → 172)
+ ~5-8 behavioral regression case
+ AGENTS Rule 9 (`no generic try/except Exception`) ihlali yoksa zaten
  spot kalkar; bu kalem onu doğal olarak temizler

**Bilinçli hariç.** `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-
typeerror-catch]`'in error-message-content tarafı (operator-facing
metin standardı) bu PR'a DAHİL EDİLMEZ — onun yeri
`[FOLLOWUP codex-automation-6]` (UI failure taxonomy, W16+ NEEDS-DESIGN).

### W15-2 scope — Workspace symlink check order / orphan removal

**Pull source.** `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-
order]`.

**Hedef.** `clean_workspace()` helper'ının symlink check sırası TOCTOU
window'u açıyor (Codex audit notu). İki seçenek:

(a) Helper kullanılmıyorsa dead code olarak sil (önce reference scan
    `rg -n "clean_workspace" --type py` ile teyit).
(b) Helper kullanılıyorsa: `lstat` → resolve → `realpath` sırasını
    workspace helper'larındaki W8-9 deseni ile aynı sıralamaya getir
    (resolve önce, çünkü symlink target güvenilmez).

**Etkilenen yollar.**

+ [executor/flows/playwright/workspace/](../../executor/flows/playwright/workspace/)
  (helper modüller; `clean_workspace`'in yaşadığı dosya scan ile teyit)
+ Olası caller'ları: `executor/flows/playwright/reset_state.py`,
  `executor/flows/playwright/automation.py`

**Adımlar.**

1. Reference scan: `clean_workspace`'in çağrıldığı yerleri bul.
2. Eğer 0 caller: dead code; sil. Test: import-graph gate'i tetiklemediğini
   doğrula.
3. Eğer caller var: TOCTOU sırasını W8-9 deseni ile hizala. Yeni
   behavioral test `tests/security/test_workspace_symlink_toctou.py`
   (symlinked path adversarial fixture).

**Test paterni.** Eğer fix path'i: behavioral test (symlink fixture +
race window simülasyonu). Eğer remove path'i: yeni test gerekmez, dead
code removal commit'i.

**Exit kriterleri.**

+ Helper ya silinir ya da TOCTOU-safe re-write edilir.
+ Eğer fix: ~3-5 case'lik behavioral test + (opsiyonel) architecture
  gate (workspace helper'larda `lstat`'tan önce `resolve` zorunlu).

**Bilinçli hariç.** Genel workspace TOCTOU sweep (yalnızca M12 path'i;
`[FOLLOWUP w8-9-network-body-boundary-split-secret-test]` ayrı).

### W15-3 scope — `activationEvents` bounds + DB field-length migration

**Pull source.** `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]`.

**Hedef.** `activationEvents` liste/string boyutu unbounded — saldırgan
manifest gigabyte-scale `activationEvents` push edebilir, DB row inflate
olabilir, oversize string parsing slowdown. Cap + DB field-length
Alembic migration.

**Etkilenen yollar.**

+ [packages/analysis_contracts/contracts.py](../../packages/analysis_contracts/contracts.py)
  — `activationEvents` field'ı (varsa) bound + `max_length`
+ Veya `appcore/contracts/schema_defs/` — DB schema'ya yansıyan
  contract
+ `alembic/versions/` — yeni migration: `activation_events` column
  (varsa) length bound; eğer text column ise constraint check
+ DB model: `appcore/db/models/` veya `appcore/storage/model_defs/`
  — Column max length

**Adımlar.**

1. Reference scan: `activationEvents` neresinde kontrat, neresinde DB
   column? (TEXT mi VARCHAR(N) mi şu an?)
2. Adversarial input scan: production scan örneği var mı (oversized
   activationEvents)?
3. Cap kararı: per-event string length ve list length. `activationEvents`
   resmi spec'te ne dökümante? (VS Code marketplace spec).
4. Pydantic v2 `max_length` + `min_length` + list `max_length`.
5. Alembic migration: `op.alter_column` ile column type değişikliği veya
   constraint check.
6. Migration round-trip: `alembic upgrade head` + `alembic downgrade -1`
   manuel doğrulama (programmatic test
   `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` deferred kalır).
7. Architecture gate: `tests/architecture/test_activationevents_bounds.py`
   (W14-2 paterni — Pydantic field'ında bound zorunlu).

**Test paterni.** Adversarial input regression (oversized list,
oversized string per item, NaN / None / non-list types) + Alembic
migration sanity (manuel doğrulama notu).

**Exit kriterleri.**

+ 1 yeni architecture gate (`tests/architecture/` 172 → 173)
+ ~6-10 behavioral regression case
+ Alembic migration landed, both directions test edildi (manuel)
+ DB field length değiştiyse: production-data scan + migration
  reversibility notu PR description'a eklenir

**Bilinçli hariç.** Genel manifest field bounds sweep — bu PR sadece
`activationEvents`. `displayName`, `description`, `keywords` vb. ayrı
W16+ aday (henüz Codex audit kalemi yok).

**Risk.** **Orta.** Migration; production-data shape kontrol etmeden
PR open etme. Eğer column'un mevcut max value'su yeni cap'ten büyükse
data truncation → veri kaybı; bound'u önce mevcut max value'ya göre
ayarla (cap >= max(current_lengths) + güvenlik tampolu).

### W15-4 scope — UI bounds bundle: event spread / timeline / relations graph cap

**Pull source.**

+ `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]`
+ `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]`

**Hedef.** İki kalem aynı patern: UI client-side büyük activation report
render ederken event density / timeline spread / relations graph
node-edge sayısı unbounded; UI freeze veya yavaş render. Cap + truncation
indicator.

**Etkilenen yollar.**

+ [ui/src/lib/](../../ui/src/lib/) view-model katmanı (özellikle
  `view-models.ts` — hand-maintained, generated değil)
+ UI component'ler: timeline view, relations graph view (lokasyon ui/
  scan ile)
+ Generated [`ui/src/lib/types/contracts.ts`](../../ui/src/lib/types/contracts.ts)
  bu PR'da değişmez (cap UI-side, backend contract aynı kalır)

**Adımlar.**

1. UI scan: timeline render edilen component, relations graph render
   edilen component, event list paginate eden component'ler.
2. Cap kararı: UI ergonomic upper bound (kullanıcı 1000+ event'i
   anlamlı şekilde inspect etmiyor; cap 500-1000 arası + scrollable
   truncation indicator).
3. View-model layer'da slice + "X more, truncated" indicator (UX
   pattern; backend cap değil).
4. Relations graph: node + edge cap; force-graph render edilen
   component'in input boundary'sinde slice.
5. UI vitest: cap enforcement + truncation indicator.

**Test paterni.**

+ UI vitest (existing `ui/src/**/*.test.ts(x)` deseni).
+ Snapshot for truncation indicator.

**Exit kriterleri.**

+ UI cap enforced + truncation UX
+ UI vitest coverage: ~5-8 case per cap (event / timeline / relations)
+ Backend contract unchanged

**Bilinçli hariç.** Backend report-side trim (backend zaten W14-2'de
ts bound + W14-3'te summary redaction yaptı; cap UI-side). Eğer backend
de truncation policy ister, ayrı W16+ pull.

### W15-5 scope — Quick fixes bundle: UI `/health` proxy + lifecycle regex

**Pull source.**

+ `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]`
+ `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]`

**Hedef.** İki düşük-blast quick fix:

**I2.** UI client'ı `/health` fetch'ini direkt API portuna gönderiyor
olabilir (nginx `/api/*` proxy'sini bypass ediyor); reverse-proxy
posture ile uyumsuz. Doğrula + fix: UI tüm fetch'leri `/api/*`
prefix'i üzerinden yapsın.

**I4.** Lifecycle log'ları "for <id>" regex'i çok geniş — bazı log
satırlarında false-match. Regex'i daralt (örn. `for [0-9a-f]{8}-` veya
job-id format'ına özel).

**Etkilenen yollar.**

+ I2: [ui/src/](../../ui/src/) — fetch utility, base URL config
+ I4: [appcore/storage/crud_ops/analysis_jobs/lifecycle.py](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py)
  veya `extrace.*` log filter'ında regex (regex location scan)

**Adımlar.**

1. I2: UI fetch scan; `/health` çağrısının base URL'ini doğrula. nginx
   proxy config (`docker/ui/nginx.conf` veya benzeri) ile uyumla.
2. I2 test: UI vitest — fetch mock'unda `/health` yerine `/api/health`
   beklentisi.
3. I4: regex location scan (`rg -n 'for <id>' --type py`); regex'i
   daralt + unit test (positive + negative case'ler).

**Test paterni.** I2 için UI vitest; I4 için unit test (Python regex).

**Exit kriterleri.**

+ I2 fixed + UI vitest case
+ I4 regex tightened + ~4-6 unit test case (positive match + false
  positive reject)

**Bilinçli hariç.** Genel UI fetch surface sweep (I2 sadece `/health`);
genel log regex sweep (I4 sadece "for <id>").

### W15-6 scope — Unauthenticated catalog endpoints posture (ADR 0011)

**Pull source.** `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-
endpoints]` (ADR pending).

**Hedef.** Catalog endpoint'leri (extension_catalog router) auth'suz —
single-host appliance scope altında bu OK mi, yoksa marker-based auth
ister mi? Karar ADR 0011 ile, sonra koda uygulanır.

**Etkilenen yollar.**

+ Yeni: `documents/adrs/0011-unauthenticated-catalog-endpoints-posture.md`
  (W15-6 close-out tespit etti: original scope-skeleton text `documents/decision-records/`
  diye yazmıştı, gerçek dizin `documents/adrs/` — ADR doğru yola landed; bu satır
  back-patch ile düzeltildi)
+ [workflows/extension_catalog/router.py](../../workflows/extension_catalog/router.py)
  (posture'a göre)
+ Olası: `appcore/api/auth.py` veya benzeri (marker-based ise)
+ Yeni: `tests/architecture/test_catalog_endpoint_posture.py`
  (posture'ı gate eden test — posture shift ADR amendment ile)

**Adımlar.**

1. ADR taslağı: ADR 0001 (single-host appliance) + ADR 0007 (loopback
   default) bağlamında posture seçenekleri:
   - **Option A:** auth'suz kalsın (single-host scope; loopback default;
     network reachable ancak `EXTRACE_ALLOW_LAN` opt-in ile).
   - **Option B:** marker-based auth (HMAC harness marker'ı W13-1'de
     landed; aynı pattern'i catalog'a uygula).
   - **Option C:** session-based auth (gereksiz karmaşıklık; tek-kullanıcı
     appliance için overkill — muhtemel ret).
2. Trade-off analizi: threat model (ADR 0002), single-host scope
   (ADR 0001), loopback default (ADR 0007).
3. Karar + ADR landed.
4. Posture'a göre kod uygula:
   - A: hiçbir kod değişikliği gerekmez; ADR cite ederek mevcut durumu
     dökümante et + posture gate'i yaz.
   - B: HMAC marker check'i catalog router'a ekle; W13-1 paterni mirror.
   - C: ret.
5. Yeni architecture gate `tests/architecture/test_catalog_endpoint_
   posture.py` — posture'ı pin'le.

**Test paterni.** Posture'a göre değişir. A path'i: gate basit (route
listed, no auth dependency). B path'i: gate marker check'i zorunlu kılar.

**Exit kriterleri.**

+ ADR 0011 landed (accepted + implemented date)
+ Posture'a göre kod
+ 1 yeni architecture gate (`tests/architecture/` 188 → 191 actual — `+1 gate file`
  `test_catalog_endpoint_posture.py` with 3 AST test functions; forecast band
  `173 → 174` from W15-6 first-sketch was stale by the time W15-3 + W15-4 +
  W15-5 mid-iter hygiene pulled the baseline forward to 188; back-patch refresh
  here matches §"W15 target deltas" actual count)
+ ADR 0002 threat model'ı amendment'la (eğer Option B veya C seçilirse — Option A
  seçildiği için amend gerekmedi; ADR 0011 §4 row 102 + §5'i cite eder)

**Bilinçli hariç.** Genel auth surface sweep (sadece catalog
endpoints). Marketplace endpoint'leri (`/api/marketplace/*`) ayrı
posture, bu PR'da dokunulmaz.

**Risk.** **Orta** — ADR karar yükü. Karar gerekçesi sonradan
tornaya alınamaz; iyi düşünülmüş gerekçe + threat-model bağı şart.

### W15-7 scope — Regression lock-in umbrella: compose pin + GH action pin + doc preamble refresh

**Pull source.**

+ `[FOLLOWUP compose-image-mutable-ref-pin]`
+ `[FOLLOWUP gh-action-trivy-version-pin]`
+ (post-W14 close-out audit immediate finding) doc preamble truth-state
  refresh

**Hedef.** Üç düşük-blast hijyen + lock-in kalemi:

**(a) Compose image pin.** `docker/docker-compose.yml` (veya repo root
`docker-compose.yml`):

+ `postgres:16-alpine` → `postgres@sha256:...`
+ `alpine/socat:latest` → `alpine/socat@sha256:...` (debug profile
  içinde; opt-in)

`tests/architecture/test_dockerfile_digest_pin.py` şu an Dockerfile
`FROM` satırlarını kontrol ediyor; bunu compose `image:` anahtarlarını
da kapsayacak şekilde **extend** (yeni gate açma; mevcut gate'in
scope'unu genişlet — bu W14-6 "extend, do not duplicate" disiplini).

**(b) GH action pin.** `.github/workflows/security.yml`:

+ `aquasecurity/trivy-action@master` → `aquasecurity/trivy-action@<SHA>`
  veya `aquasecurity/trivy-action@v0.X.Y` (workflow'un diğer action'larıyla
  aynı pattern).

Yeni gate gerekmez; mevcut workflow YAML lint zaten çoğu hata'yı
yakalar. Eğer ekstra invariant istenirse `tests/architecture/
test_gh_action_pinning.py` (ama önce mevcut workflow auditle
ihtiyacı doğrula).

**(c) Doc preamble truth-state refresh.** W14 close-out PR #21 merge
sonrası 4 canonical preamble'ı refresh:

+ `CLAUDE.md` (line 3)
+ `AGENTS.md` (line 3)
+ `documents/REFACTOR_STATUS.md` (line 3)
+ `documents/POST_POC_BACKLOG.md` (line 3)

"W14 close-out PR week14 -> main next" → "W14 close-out PR #21
`week14 -> main` **MERGED** `2026-05-14` via `4e03c8d`". Tarih bump.

`tests/architecture/test_readme_phase_pointer.py` zaten phase pointer
discipline'ı izliyor mu? Doğrula; eğer izlemiyorsa preamble truth-state
gate'i eklemeyi düşün (ama önce mevcut gate'in scope'unu kontrol).

**Etkilenen yollar.**

+ [docker-compose.yml](../../docker-compose.yml) (line 121 civarı —
  `alpine/socat`; postgres tag konum scan ile)
+ [.github/workflows/security.yml](../../.github/workflows/security.yml)
  (line 71 — trivy action)
+ [tests/architecture/test_dockerfile_digest_pin.py](../../tests/architecture/test_dockerfile_digest_pin.py)
  — scope extension
+ [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md),
  [documents/REFACTOR_STATUS.md](../REFACTOR_STATUS.md),
  [documents/POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md)

**Adımlar.**

1. SHA çek: postgres + socat current digest'lerini docker registry'den
   resolve et (`docker pull` + `docker inspect`).
2. Compose pin + gate extension.
3. Trivy action SHA veya version pin.
4. 4 preamble refresh (text edit).
5. Gate extension'ın yeni image entry'leri yakaladığını doğrula
   (existing gate'i koş).

**Test paterni.** Architecture gate scope extension (yeni gate açma).

**Exit kriterleri.**

+ Compose image'ler digest-pinned
+ GH action version/SHA-pinned
+ `test_dockerfile_digest_pin.py` compose `image:` anahtarlarını da
  kapsar — `tests/architecture/` count 174 (unchanged; extension, not
  new gate)
+ 4 preamble refresh'lendi
+ W14 close-out audit immediate finding kapanır

**Bilinçli hariç.** Genel mutable-ref sweep (sadece compose + trivy);
geniş GH Actions CI reintroduction (`[FOLLOWUP ci-reintroduction]`
ayrı, W16+).

## Excluded From W15 (W15+'a veya W16+'ya düşer)

+ **W14-1 sonrası deferral (W15+):**
  `[FOLLOWUP scenario-accountant-conservation-split]` — kök neden
  downgrade hâlâ geçerli, doğrudan trigger yok; defer.
+ **Codex M-class tail (W15 dışı):** M5 (W14-5 yan ürünü olarak kapandı),
  geri kalan tüm M-class kalemler W15 sub-iter slate'inde.
+ **Watching items (LoC bütçesi aşılana kadar dokunma):**
  `[FOLLOWUP planner-selection-readability-audit]`,
  `[FOLLOWUP attribution-links-build-evidence-bundle-density]`,
  `[FOLLOWUP execute-attempt-rebloat-watch]`,
  `[FOLLOWUP dispatch-execution-rebloat-watch]`.
+ **UI follow-up'ları (W15-4 dışında):**
  `[FOLLOWUP ui-raw-context-discriminator-parity]`,
  `[FOLLOWUP ui-supplemental-types-retire]`,
  `[FOLLOWUP vsix-integrity-in-activation-report]`,
  `[FOLLOWUP vsix-thresholds-extra-keys]`,
  `[BACKLOG ui-v3-5]`, `[CLEANUP ui-v3-9]`, `[CLEANUP ui-v3-14]`.
+ **Workflow / platform deferral'leri:**
  `[FOLLOWUP simulation-progress-cancel]` alt-kalemleri,
  `[FOLLOWUP analysis-thread-supervisor]`,
  `[FOLLOWUP job-service-typevar-audit]`,
  `[FOLLOWUP sqlalchemy-error-subtype-logging]`,
  `[FOLLOWUP w11-8-companion-workflow-orm-bleed]`.
+ **Contracts / detection deferral'leri:**
  `[BUG silent-scenario-dropout-regression]`,
  `[FOLLOWUP report-finalize-top-level-field-sync-drift]`,
  `[FOLLOWUP event-attempt-verification-status-validator]`,
  `[FOLLOWUP report-invariants-runtime-evidence-drift]`,
  `[FOLLOWUP compute-verdict-table-driven-test]`,
  `[FOLLOWUP signal-summary-needs-review-categories]`,
  `[FOLLOWUP monitor-types-property-recomputation]`,
  `[FOLLOWUP activation-discovery-strategy-outcome-detail]`,
  `[FOLLOWUP planner-executor-action-enum]`,
  `[CLEANUP rule-registry-side-effect-loader]` (ADR 0003 deferred
  rules A5/A7 landed olunca).
+ **Engineering quality deferral'leri:**
  `[CLEANUP report-builder-naming]`,
  `[CLEANUP monitor-runtime-naming-overlap]`,
  `[CLEANUP env-example-extrace-vars]`,
  `[CLEANUP postgres-version-fact-drift]`,
  `[CLEANUP adr-0007-runbook-wording-drift]`,
  `[CLEANUP pre-commit-python-version-alignment]`,
  `[CLEANUP test-import-graph-policy-dump-split]`,
  `[FOLLOWUP ci-reintroduction]`.
+ **Test + observability deferral'leri:**
  `[FOLLOWUP w8-0-capture-pipeline]`,
  `[FOLLOWUP w8-1-extract-rejection-logging]`,
  `[FOLLOWUP w8-1-archive-count-bypass]`,
  `[FOLLOWUP w8-1-vsix-compressed-size-limit]`,
  `[FOLLOWUP w8-3-harness-js-scheme]`,
  `[FOLLOWUP w8-4-broader-executor]`,
  `[FOLLOWUP w8-6-content-sample-structural-test]`,
  `[FOLLOWUP w8-8-manifest-emit-when-needed]`,
  `[FOLLOWUP w8-8-trigger-sweep-as-test]`,
  `[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`,
  `[FOLLOWUP adr-0002-vsix-extraction-section-missing]`,
  `[FOLLOWUP codex-automation-6]` (UI failure taxonomy, NEEDS-DESIGN
  → W16+),
  `[FOLLOWUP capability-verification-gap]` (NEEDS-DESIGN → W16+).
+ **Hijyen quick wins (opportunistic pull-as-found):** W15 close-out
  hygiene PR'ında sweep edilebilir (W14 close-out paterni: Ruff lint,
  markdown formatting, UI contract sync — eğer drift varsa).

## Test Baseline (target deltas)

W14 final baseline (re-recorded `2026-05-14` at W15-1 pull on `week15`):

+ `tests/architecture/` **172 passed** (W14-8 lifted 170 → 171;
  close-out hygiene PR ADR-code-fence gate counts as the post-merge
  +1 to 172).
+ `make test-security` **215 passed** (unchanged from W13 final).
+ `make test-local` not re-run at pull (Docker postgres_test required);
  full re-record deferred to next sub-iter that exercises cross-module
  behavior or to W15 close-out hygiene.

W15-1 actual deltas (`2026-05-14` via `c58c365`):

+ `tests/architecture/` 172 → **178** (+6 cases — new file
  `test_analyze_error_taxonomy_parity.py`: tuple decomposition, sync
  single-clause discipline, async references both subset tuples,
  helper class-branch coverage, sync handler-body dispatch through
  helper [vacuous-truth], ExecutorError branch delegates to
  `map_executor_error` [W10-7 redaction contract]).
+ New behavioral file `tests/workflows/marketplace/test_analyze_error_taxonomy.py`
  with **+21 cases** (10 helper status map incl. PermissionError
  subclass-dispatch + 1 unmapped-class guard + 1 vacuous-truth
  coverage check + 9 endpoint round-trip).
+ Existing 66 `tests/workflows/marketplace/test_router.py` cases
  unchanged (no regression in the sync surface contract).

W15-2 actual deltas (`2026-05-14` via `765cde7`; behavioral coverage
extended `2026-05-15` after rebuild+scan verification):

+ `tests/architecture/` 178 → **180** (+2 cases — new file
  `test_workspace_symlink_check_order.py`: AST line-order invariant
  pinning `is_symlink`/`islink`/`lstat` before `shutil.rmtree` across
  both workspace cleanup chokepoints; vacuous-truth guard pinning the
  helpers table to declared module paths).
+ New behavioral file `tests/security/test_workspace_symlink_toctou.py`
  with **+8 cases** (5 initial: real file / real dir /
  symlink-to-external-dir / symlink-to-external-file / dangling
  symlink; 3 post-rebuild edge cases: nested symlink in real subdir,
  idempotency on empty workspace, mixed-contents stress matrix).
+ Existing `tests/executor/test_workspace.py` + `test_reset_state.py`
  unchanged (no regression in the workspace contract).
+ **W15-3 actual deltas (`2026-05-15` via `3512a7c`; behavioral
  coverage extended post-rebuild verification):**
  + `tests/architecture/` 180 → **186** (+6 cases — new file
    `test_activationevents_bounds.py`: three Pydantic
    `max_length` invariants
    (`ExtensionActivationEventsSchema.event_type` → 64,
    `ExtensionActivationEventsSchema.event_value` → 1024,
    `ExtensionDetailSchema.activation_events` → 512); two
    SQLAlchemy `String(N)` column invariants
    (`ExtensionActivationEvents.event_type` → `String(64)`,
    `event_value` → `String(1024)`); one vacuous-truth guard
    pinning class/field/column names to declared module paths).
  + New behavioral file
    `tests/workflows/extension_catalog/test_activation_events_bounds.py`
    with **+12 cases** (8 initial: 3 boundary acceptance at
    64 / 1024 / 512 + 3 one-over rejection raising
    `ValidationError` + 2 parser-level defense-in-depth — slice
    a 600-event list at 512, skip an event whose `event_value`
    exceeds 1024 chars; +4 edge cases post-rebuild: missing
    `activationEvents` key returns `None`, non-list value
    returns `None`, no-colon event over the `event_type` cap is
    skipped, exact-512 list passes the slice unmodified).
  + Existing `tests/workflows/extension_catalog/` 67 passed, no
    regression in the catalog ingestion contract.
  + Manual Alembic round-trip (postgres_test) deferred to operator
    at land; programmatic round-trip stays under
    `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]`.
+ **Production verification `2026-05-15` 12:16** — operator
  rebuilt the API container via `make rebuild` (after the
  Makefile fix at `203d653` made `rebuild` recreate-aware) and
  ran a fresh UI scan against
  `ms-python.python@2026.5.2026051301`. Result identical to the
  `2026-05-14` 15:15 baseline (and to the `2026-05-15` 09:51 /
  11:26 mid-iter checkpoints) on every critical field
  (`target_extension_observed True`, `risk_signals 0`,
  `run_quality low`, `signal_summary.score 28` /
  `level needs_review`, `automation_health.status degraded`
  with the same 4 reasons, same 5 requested / 3 traced / 0
  failed / 2 skipped scenarios, same `verification_gap 2`,
  same 22 `activated` entries with byte-equal
  `(extension_id, activation_event)` sequence, 21 event
  attempts, 12 output signal events). Numerical jitter within
  the established peer-extension noise window
  (`evidence_events` 2804, `network_events` 163, `file_events`
  2541, `process_events` 63 — all inside the
  ±0.1-6 % envelope of the four-scan baseline). No drift
  attributable to the W15-3 changes; deployment is green.
  + Recorded cold-start anomaly at `2026-05-15` 12:01 (first
    scan ~5 min post-recreate): `signal_summary.score` 14,
    `activated` 20, inflated `file_events 3685` /
    `evidence_events 3971` / `network_events 207`, depressed
    `process_events 44`. Resolved by the 12:16 follow-up scan
    once peer extensions completed activation. Tracked as a
    post-rebuild stabilization characteristic; unrelated to
    W15-3 cap behavior.
+ **Runtime cap verification (container introspection,
  `2026-05-15` 11:54).** Inside the rebuilt
  `automation_api` container:
  `workflows.extension_catalog.manifest_parser._MAX_ACTIVATION_EVENTS == 512`,
  `_MAX_ACTIVATION_EVENT_TYPE_LEN == 64`,
  `_MAX_ACTIVATION_EVENT_VALUE_LEN == 1024`;
  Pydantic field metadata reports
  `MaxLen(64)` / `MaxLen(1024)` / `MaxLen(512)` on
  `event_type` / `event_value` /
  `ExtensionDetailSchema.activation_events`; `alembic current`
  resolves to `e7c0a8f3b9d2 (head)` (the W15-3 migration was
  auto-applied at container start).
+ **Production verification `2026-05-15` 09:51** — operator rebuilt
  the executor container (image carrying `week15` HEAD with W15-1 +
  W15-2 in it) and ran a fresh UI scan against
  `ms-python.python@2026.5.2026051301`. Result identical to the
  `2026-05-14` 15:15 baseline on every critical field
  (target_extension_observed True, risk_signals 0, run_quality low,
  signal_summary.score 28, automation_health.status degraded with the
  same 4 reasons, same 3 completed scenarios + same 2 dropouts,
  same 2 capability verification gaps). Metric jitter ±2% on event
  counts; ``correlated_only_event_count`` 41 → 31 — minor improvement
  (peer-extension noise timing) but not a regression direction. No
  drift attributable to the W15-1 / W15-2 changes; deployment is
  green.

W15 target deltas (per sub-iter):

| Iter | `tests/architecture/` delta | Behavioral test delta | Net |
|---|---|---|---|
| W15-1 ✅ | **+6 (actual)** sync-async parity (6 invariants — 4 initial + 2 post-W15-1 strengthening: handler-body dispatch + ExecutorError delegation) | +21 case (helper + endpoint parametrize + PermissionError subclass) | **closed +6 gates** |
| W15-2 ✅ | **+2 (actual)** workspace cleanup symlink-check order + helpers-table pin | +8 case (5 initial: real file/dir + 3 adversarial symlink fixtures; +3 edge: nested symlink in real subdir + idempotency + mixed-contents stress) | **closed +2 gates** |
| W15-3 ✅ | **+6 (actual)** activationEvents bounds gate (3 Pydantic `max_length` + 2 SQLAlchemy `String(N)` + 1 vacuous-truth target table) | +12 case (3 boundary OK + 3 one-over reject + 2 parser-level defense-in-depth + 4 parser-level edge cases: 2 type-guard regression + 1 oversized no-colon skip + 1 exact-512 boundary) | **closed +6 gates** |
| W15-4 | +0 (UI-side, architecture gate yok) | +3 dosya UI vitest (~15-24 case) | +0 arch |
| W15-5 ✅ | **+0 (actual)** matches forecast — W14-6 "extend, do not duplicate" check (no existing `apiClient` URL prefix gate, no existing `_LIFECYCLE_MARKER_PATTERNS` shape gate) deferred new gates to W15-7 close-out hygiene | **+14 case** (3 backend pytest in `tests/test_health.py` — legacy `/health` + new `/api/health` + payload-equality cross-check; 2 UI vitest in new `ui/src/lib/api/client.test.ts` — fetch-spy URL discipline; 9 parser unit in `tests/executor/test_playwright_extension_host.py` — 4 positive parametrize for the tightened `<publisher>.<name>` shape + 5 negative parametrize for the pre-W15-5 false-positive shapes the loose regex tolerated) | **closed +0 gates** |
| W15-6 ✅ | **+1 (actual)** new gate file `test_catalog_endpoint_posture.py` with 3 AST test functions (docstring cite + no auth dependency + endpoint-count lock at 12); W14-6 "extend, do not duplicate" check found no extendable gate covering router posture invariants | **+3 case** (matches +1 gate file accounting; pytest reports 188 → 191 reflecting the three function instances) | **closed +1 gate** (Option A — ADR 0011 Accepted; ADR 0002 NOT amended) |
| W15-7 | +0 (mevcut gate extension) | (extension, yeni dosya yok) | +0 (extension) |
| **Total** | **+3 ile +4 arası** | **~35-60 behavioral case** | `tests/architecture/` 171 → **174-175** |

`make test-local` ve `make test-security` delta'sı sub-iter close'larından
sonra re-record edilir (W14 paterni: her sub-iter sonu test sayısını
bottom-of-file summary'ye eklenir).

## Per-Item Detail (filled in as sub-iters close)

### W15-1 — Sync analyze error taxonomy parity with async path — closed `2026-05-14` via `c58c365`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]`.

**Landing commit(s).** `c58c365` (single atomic commit — production +
arch gate + behavioral test).

**Module locations.**

+ `workflows/marketplace/analysis_service.py:77-103` — three module-level
  tuples `ANALYZE_RECOVERABLE_ERROR_TYPES`,
  `ANALYZE_PROGRAMMING_ERROR_TYPES`, `ANALYZE_ERROR_TYPES` (union as
  `BinOp(Add)` over the two subset names).
+ `workflows/marketplace/analysis_service.py:218-256` —
  `analyze_error_to_http_response(exc)` helper with isinstance branches
  for ExecutorError (delegates to `map_executor_error`),
  FileNotFoundError, ActivationReportLoadError/TriggerPlanError/OSError/
  SQLAlchemyError, ValueError, TypeError/AttributeError.
+ `workflows/marketplace/analysis_service.py:368-379` — async
  `run_analysis_job` except clauses migrated to
  `ANALYZE_PROGRAMMING_ERROR_TYPES` / `ANALYZE_RECOVERABLE_ERROR_TYPES`
  (replaces the prior open-coded six-class + two-class tuples).
+ `workflows/marketplace/router.py:328-345` — sync `analyze_extension`
  collapses the prior four-clause except into one
  `except ANALYZE_ERROR_TYPES` over the helper.

**Tests added.**

+ `tests/architecture/test_analyze_error_taxonomy_parity.py` × **6** AST
  invariants:
    1. Tuple decomposition (`ANALYZE_ERROR_TYPES = ANALYZE_RECOVERABLE_ERROR_TYPES + ANALYZE_PROGRAMMING_ERROR_TYPES`).
    2. Sync `analyze_extension` single-clause discipline (only
       `except ANALYZE_ERROR_TYPES`).
    3. Async `run_analysis_job` references both subset tuples.
    4. Helper has isinstance branch for every taxonomy class.
    5. **(post-W15-1)** Vacuous-truth — sync handler body dispatches
       through `analyze_error_to_http_response`; no open-coded
       `HTTPException(...)` inside the except body. Prevents a refactor
       from keeping invariant 2 (canonical tuple) while routing the
       caught exception through a hand-rolled status map.
    6. **(post-W15-1)** ExecutorError branch in the helper delegates to
       `map_executor_error` — pins the W10-7 secret-redacted detail +
       structured `error_id` contract so the branch cannot regress into
       a plain inline `HTTPException(502, str(exc))`.
+ `tests/workflows/marketplace/test_analyze_error_taxonomy.py` × **21**
  cases:
  + Parametrized helper status map × **10** (9 taxonomy classes +
    `PermissionError` subclass-dispatch case — verifies `isinstance`
    MRO so `PermissionError` lands on the `OSError` 502 branch
    without an exact-type match).
  + Unmapped-class defensive guard × 1
    (synthetic `RuntimeError` subclass trips the helper's
    `AssertionError`).
  + Vacuous-truth coverage check × 1 (every class in
    `ANALYZE_ERROR_TYPES` appears at least once in `HELPER_CASES`).
  + Endpoint round-trip via TestClient × **9** (HELPER_CASES minus
    ExecutorError — its detail body is asserted by existing
    `test_analyze_install_failure_502` /
    `test_analyze_automation_failure_502`; `PermissionError` included
    and routes to 502 end-to-end).

**Production diff.** +50 net LoC in `analysis_service.py` (tuples +
helper + import + `__all__`); −10 net LoC in `router.py` (four-clause
except collapsed; unused imports dropped). Net +40 LoC production +592
LoC including tests/docs.

**Verification.**

+ `make test-security` **215 passed** (no drift; W13 / W14 baseline).
+ `pytest tests/architecture/` **176 passed** (W14 final 172 + W15-1
  +4).
+ `pytest tests/workflows/marketplace/test_router.py` 66 passed, 1
  skipped (fixture-availability skip, unrelated).
+ `pytest tests/workflows/marketplace/test_analyze_error_taxonomy.py`
  19 passed.
+ `ruff check workflows/marketplace/ tests/architecture/test_analyze_error_taxonomy_parity.py tests/workflows/marketplace/test_analyze_error_taxonomy.py` — clean.
+ `make test-local` not re-run (Docker postgres_test required); full
  baseline re-record deferred to a later sub-iter that needs the
  Docker-backed lane, or to W15 close-out hygiene.

**Status map (mirrors async `fail_job` semantics).**

| Exception | Sync (pre-W15-1) | Sync (post-W15-1) | Async (run_analysis_job) |
|---|---|---|---|
| ExecutorError | 502 (map_executor_error) | 502 (unchanged via helper delegation) | fail_job |
| FileNotFoundError | 404 | 404 | fail_job (recoverable) |
| ActivationReportLoadError | 502 | 502 (helper matches before ValueError branch) | fail_job (recoverable; via ValueError catch) |
| TriggerPlanError | 502 | 502 | fail_job (recoverable) |
| OSError | **500 (bubble)** | **502** | fail_job (recoverable) |
| SQLAlchemyError | **500 (bubble)** | **502** | fail_job (recoverable) |
| ValueError | **500 (bubble — non-ARLE)** | **400** | fail_job (recoverable) |
| TypeError | **500 (bubble)** | **500 (explicit)** | fail_job + re-raise (programming) |
| AttributeError | **500 (bubble)** | **500 (explicit)** | fail_job + re-raise (programming) |

**Consciously excluded (defers to W16+).** Error-message-content
operator-facing standard for the M10 follow-up → tracked under
`[FOLLOWUP codex-automation-6]` (UI failure taxonomy, NEEDS-DESIGN).

### W15-2 — Workspace cleanup `is_symlink` ordering — closed `2026-05-14` via `765cde7`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]`.

**Landing commit(s).** `765cde7` (single atomic commit covering
production code, the arch gate, and the behavioral test).

**Path taken.** (b) **fix** — not (a) dead-code removal.
``rg -n "clean_workspace" --type py`` showed a live production caller
at ``executor/flows/playwright/reset_state.py:176`` (plus 6 test
references in ``tests/executor/test_reset_state.py``); the helper is
not orphan code so the removal path was not available.

**Root cause.** Pre-W15-2 ``clean_workspace`` branched on ``is_dir()``
(which follows symlinks) before falling through to ``shutil.rmtree``:

```python
for child in WORKSPACE_DIR.iterdir():
    if child.is_dir():
        shutil.rmtree(child)   # raises OSError on a symlink in Py ≥3.7
    else:
        child.unlink()
```

A symlink-to-directory inside the workspace caused
``shutil.rmtree(child)`` to raise ``OSError`` (Python ≥3.7 refuses to
rmtree a symlink), leaving the workspace partially cleaned. The
adversarial broader concern is that the symlink target is
operator-controlled state outside the workspace that automation
cleanup must never touch.

**Module locations.**

+ `executor/flows/playwright/workspace/__init__.py:74-92` —
  ``clean_workspace`` now mirrors the established
  ``_clear_directory`` pattern (``reset_state.py:43-55``):
  ``is_symlink() or is_file()`` -> ``unlink()`` (link entry removed,
  target untouched); else -> ``shutil.rmtree`` (safe because the
  symlink branch has already filtered out symlinks).
  ``Path.is_symlink()`` is backed by ``lstat`` and does not follow
  the link.

**Tests added.**

+ `tests/architecture/test_workspace_symlink_check_order.py` × **2**
  AST invariants:
    1. Every cleanup chokepoint in ``WORKSPACE_HELPERS`` (currently
       ``clean_workspace`` + ``_clear_directory``) classifies
       symlink-ness via ``is_symlink`` / ``islink`` / ``lstat`` at an
       earlier AST line number than its earliest ``shutil.rmtree``
       call.
    2. Vacuous-truth — every helper named in ``WORKSPACE_HELPERS``
       must resolve to a real ``FunctionDef`` at its declared module
       path (rename detection).
+ `tests/security/test_workspace_symlink_toctou.py` × **8** behavioral
  cases:
  + Real file removal (sanity).
  + Real dir recursive removal (sanity).
  + Symlink-to-external-dir: link unlinked, target dir + contents
    survive byte-equal.
  + Symlink-to-external-file: link unlinked, target file content
    survives byte-equal.
  + Dangling symlink: unlinked without raising
    (post-W15-2 is intentional via ``is_symlink`` branch; pre-W15-2
    worked by accident via the ``unlink()`` fall-through).
  + Nested symlink inside real subdir: ``shutil.rmtree`` recurses
    into the real subdir without following an inner
    symlink-to-external (pins Python's default ``followlinks=False``
    contract; guards against a future refactor to
    ``rmtree(..., followlinks=True)`` or ``os.walk(followlinks=True)``).
  + Idempotency: calling ``clean_workspace`` twice on an empty
    workspace is a no-op (pins the contract so a future refactor
    cannot add a "must be non-empty" precondition).
  + Mixed-contents stress: regular file + real dir + symlink-to-dir
    + symlink-to-file + dangling symlink in a single workspace; one
    cleanup pass removes every entry and preserves every external
    target byte-equal.

**Production diff.** +9 net LoC in
``executor/flows/playwright/workspace/__init__.py`` (8 LoC comment
explaining the invariant + 2 LoC fix replacing 2 LoC; net +9 because
the pre-state had no comment).

**Verification.**

+ `pytest tests/architecture/test_workspace_symlink_check_order.py`
  2 passed.
+ `pytest tests/security/test_workspace_symlink_toctou.py` 5 passed.
+ `pytest tests/executor/test_workspace.py tests/executor/test_reset_state.py`
  14 passed (no regression in workspace contract).
+ `pytest tests/architecture/` collects **180** (W15-1 final 178 + 2).
+ `ruff check executor/flows/playwright/workspace/ tests/architecture/test_workspace_symlink_check_order.py tests/security/test_workspace_symlink_toctou.py` — clean.

**Consciously excluded (defers to W16+).** Generic TOCTOU sweep across
all workspace helpers; this PR is scoped only to the M12 path.
``[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`` is a
separate concern.

### W15-3 — `activationEvents` size caps + DB field-length migration — closed `2026-05-15` via `3512a7c`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]`.

**Landing commit(s).** `3512a7c` (single atomic commit covering
production code on three surfaces, the Alembic migration, the
architecture gate, and the behavioral test).

**Root cause.** Pre-W15-3 the VS Code manifest field `activationEvents`
was unbounded across three ingestion surfaces — the Pydantic ingest
schema (`ExtensionActivationEventsSchema`,
`ExtensionDetailSchema.activation_events`), the manifest pre-parser
(`workflows/extension_catalog/manifest_parser.py:parse_activation_events`),
and the DB columns
(`ExtensionActivationEvents.event_type` / `event_value` both declared
plain `String`). A hostile manifest could push gigabyte-scale data
through ingestion, inflating DB rows and slowing parse. VS Code spec
documents no numeric limits; production fixtures under
`tests/platform/contracts/fixtures/activation_reports/` show
single-digit list lengths and ≤50-char events, so every cap below is
loose enough never to reject a real extension.

**Module locations.**

+ `appcore/contracts/schema_defs/catalog.py:29-33` —
  `ExtensionActivationEventsSchema.event_type` declared
  `Field(..., max_length=64)`; `event_value` declared
  `Field(default=None, max_length=1024)`.
+ `appcore/contracts/schema_defs/catalog.py:187-189` —
  `ExtensionDetailSchema.activation_events` declared
  `Field(default_factory=list, max_length=512)` (Pydantic v2 list
  cap).
+ `workflows/extension_catalog/manifest_parser.py:8-14` —
  module-level mirror constants `_MAX_ACTIVATION_EVENTS = 512`,
  `_MAX_ACTIVATION_EVENT_TYPE_LEN = 64`,
  `_MAX_ACTIVATION_EVENT_VALUE_LEN = 1024`.
+ `workflows/extension_catalog/manifest_parser.py:82-103` —
  defense-in-depth pre-filter: slice `activation_events[:512]`
  before the parse loop; inside the loop, `continue` if the event's
  split (`event_type`, `event_value`) would exceed the per-string
  caps. Stops oversized inputs from reaching Pydantic at all;
  Pydantic remains the safety net for any path bypassing this
  parser.
+ `appcore/storage/model_defs/extension.py:152-153` —
  `ExtensionActivationEvents.event_type` declared
  `mapped_column(String(64), nullable=False, index=True)`;
  `event_value` declared
  `mapped_column(String(1024), nullable=True)`.
+ `alembic/versions/e7c0a8f3b9d2_bound_activation_events_columns.py`
  — upgrade alters `event_type` / `event_value` via
  `op.alter_column(..., type_=sa.String(64|1024),
  postgresql_using='substring(col, 1, N)')`; downgrade restores
  unbounded `sa.String()` types.

**Tests added.**

+ `tests/architecture/test_activationevents_bounds.py` × **6** AST
  invariants:
    1. `ExtensionActivationEventsSchema.event_type` declared with
       `Field(..., max_length=64)`.
    2. `ExtensionActivationEventsSchema.event_value` declared with
       `Field(..., max_length=1024)`.
    3. `ExtensionDetailSchema.activation_events` declared with
       `Field(..., max_length=512)` on a list-typed field.
    4. DB column `event_type` declared as
       `mapped_column(String(64), ...)` in `model_defs/extension.py`.
    5. DB column `event_value` declared as
       `mapped_column(String(1024), ...)` in
       `model_defs/extension.py`.
    6. Vacuous-truth — every (class, attribute) target above must
       resolve to a real annotated field at its declared module
       path (rename detector; forces a table update on rename so
       invariants 1-5 cannot pass vacuously).
+ `tests/workflows/extension_catalog/test_activation_events_bounds.py`
  × **12** cases:
  + Boundary acceptance × 3 (`event_type` at 64 chars;
    `event_value` at 1024 chars; list at 512 entries — all
    accepted by Pydantic).
  + One-over rejection × 3 (each axis trips `ValidationError`:
    `event_type` 65 chars, `event_value` 1025 chars, list of
    513).
  + Parser-level defense-in-depth × 2 (a 600-event list returns
    512 after parser slice; an event whose `event_value` would
    exceed the per-string cap is silently dropped, matching the
    existing tolerant `continue` style for non-`str` events).
  + Parser-level edge cases × 4 (added post-rebuild
    verification): missing `activationEvents` key returns
    `None`; non-list `activationEvents` value (e.g. a raw
    string) returns `None`; a no-colon event over the
    `event_type` cap is skipped (mirrors the colon branch's
    oversize-skip); an exact-512 list passes the parser slice
    unmodified (pins `[:512]`, not `[:511]`).

**Cap rationale (recorded for posterity).**

+ `event_type` 64: VS Code event taxonomy ~25 names, longest known
  ~30 chars; 2× buffer; matches the 64-char tag-field precedent at
  `packages/analysis_contracts/evidence.py:180`.
+ `event_value` 1024: worst-case legitimate
  `onCommand:<publisher>.<name>.<command>` ≈ 260 chars (npm
  package-name rules bound publisher + name at 214 chars; extras
  land under 260); 4× buffer; comfortably above any sensible
  `workspaceContains` glob.
+ list 512: heavy real-world extensions top out ~100 events
  (language packs, multi-feature toolkits); 5× margin keeps the
  99.9th-percentile tolerant; worst-case payload
  512 × (64 + 1 + 1024) ≈ 545 KiB — bounded, three orders of
  magnitude under gigabyte-scale.

**Verification.**

+ `pytest tests/architecture/test_activationevents_bounds.py` 6
  passed.
+ `pytest tests/workflows/extension_catalog/test_activation_events_bounds.py`
  8 passed.
+ `pytest tests/architecture/` collects **186** (W15-2 final 180 +
  6).
+ `pytest tests/workflows/extension_catalog/` 67 passed, 0 failed —
  no regression in the catalog ingestion contract.
+ `ruff check
  appcore/contracts/schema_defs/catalog.py
  appcore/storage/model_defs/extension.py
  workflows/extension_catalog/manifest_parser.py
  alembic/versions/e7c0a8f3b9d2_bound_activation_events_columns.py
  tests/architecture/test_activationevents_bounds.py
  tests/workflows/extension_catalog/test_activation_events_bounds.py`
  — clean.
+ Manual Alembic round-trip against `postgres_test` (operator-run
  at land): `\d extension_activation_events` should show
  `event_type character varying(64) NOT NULL` and
  `event_value character varying(1024)`; downgrade should restore
  unbounded `character varying` types.

**Consciously excluded (defers to W16+).**

+ `TriggerScenarioDetail.activation_events`
  (`packages/analysis_contracts/contracts.py:408`) — a different
  surface (per-scenario analysis *output*, not manifest
  *ingest*). No Codex audit row points here; W16+ candidate only
  if a future audit flags it.
+ Other unbounded manifest fields (`displayName`, `description`,
  `keywords`, `categories`, `icon`, `main`, `browser`) — Codex
  audit item U8 is `activationEvents`-only; W16+ candidate if a
  future audit surfaces a generalised manifest field bounds sweep.
+ Programmatic Alembic round-trip test — explicit defer under
  `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]`.

### W15-4 — UI bounds bundle: timeline / density strip / relations graph caps — closed `2026-05-16` via `89e13e3`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]`,
plus `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]`.

**Landing commit(s).**

+ `89e13e3` — UI implementation: new `ui/src/lib/displayCaps.ts`
  helper + constants, `EventTimeline` cap + indicator, extracted
  `EventDensityStrip` with cap + indicator, `ReportsPage` import
  swap and `+N groups not shown` Eyebrow in
  `InteractionsSection`, `InteractionGraph` literal-to-`DISPLAY_CAPS`
  swap, and 3 new vitest files (`displayCaps.test.ts`,
  `EventTimeline.test.tsx`, `EventDensityStrip.test.tsx`).
+ `976dc96` — post-slate W15-1 typing hotfix surfaced by the W15-4
  close-out `make typecheck` run; tightens
  `ANALYZE_*_ERROR_TYPES` annotations from
  `tuple[type[BaseException], ...]` to `tuple[type[Exception], ...]`
  in `workflows/marketplace/analysis_service.py` so the helper
  `analyze_error_to_http_response(exc: Exception)` accepts the
  except-bound `exc` at
  `workflows/marketplace/router.py:341`. Zero runtime behavior
  change (tuple members are all `Exception` subclasses already);
  W14-7 hotfix precedent (`df925f8`).

**Root cause.** Pre-W15-4 the three UI views in the extension
activation report had no display-side cap. Production scan
`output/activation_report_ms-python.python-…-e260e3e13dab.json`
(2026-05-16 19:43) carries **2,803 `evidence_events`** + **3,813
`evidence_links`** — comfortably enough to freeze the SVG renders.
`EventTimeline` rendered every event as its own `<g>` marker;
`EventDensityStrip` (inline in `ReportsPage`) fed every event into
`Math.ceil(maxT)` 1-second buckets;
`InteractionsSection`'s `Panel "Interaction graph"` surfaced the
existing leaf-overflow indicator (`InteractionGraph.tsx:55`) but no
top-level groups overflow indicator. Backend report-side trim was
out of scope per the W15-4 scope lock (W14-2 ts bound + W14-3
summary redaction already handled the report-side caps; W15-4 is
view-policy only).

**Module locations.**

+ `ui/src/lib/displayCaps.ts` (new, 44 LOC) —
  `DISPLAY_CAPS` const-asserted object exporting
  `TIMELINE_EVENTS=800`, `EVENT_DENSITY_EVENTS=800`,
  `RELATIONS_GROUPS=5`, `RELATIONS_LEAVES_PER_GROUP=6` (last two
  value-preserving against the existing `InteractionGraph.tsx`
  literals so the swap is semantic-identity); generic
  `applyDisplayCap<T>(items, cap): CappedList<T>` slice-with-
  overflow primitive (handles `cap=0` defensively and preserves
  array reference identity when below the cap); standardised
  `formatTruncationLabel(c, noun?='items')` for the timeline-style
  copy `+N more · showing first X of Y NOUN · filter to narrow`.
+ `ui/src/features/reports/charts/EventTimeline.tsx:64-95` —
  `allEvents` memo split into `normalizedEvents` (filter +
  chronological sort) → `cappedEvents = applyDisplayCap(…, 800)`;
  visible markers carry `data-testid="timeline-event-marker"`;
  header `<span>` wrapped in a flex container with truncation
  indicator span (`data-testid="timeline-truncation-indicator"`)
  emitted via `formatTruncationLabel(…, "events")` only when
  `cappedEvents.truncated`.
+ `ui/src/features/reports/charts/EventDensityStrip.tsx` (new
  extract, 116 LOC) — pure refactor of the inline
  `EventDensityStrip` previously at
  `ReportsPage.tsx:674-745` plus `applyDisplayCap(events, 800)`
  before bucket computation; bucket buttons carry
  `data-testid="density-bucket"`; truncation row at the end
  (`data-testid="density-truncation-indicator"`) reads
  `+N events truncated · density reflects first 800 of M` only
  when `capped.truncated`.
+ `ui/src/features/reports/ReportsPage.tsx` — inline
  `EventDensityStrip` removed (-72 LOC), `./charts/EventDensityStrip`
  import added; `InteractionsSection` (around line 529-575) adds
  `right` slot on the "Interaction graph" `Panel` carrying an
  `Eyebrow` wrapped in
  `<span data-testid="interaction-groups-truncation-indicator">`
  when `graph.groups.length > DISPLAY_CAPS.RELATIONS_GROUPS`
  (copy: `+N groups not shown`).
+ `ui/src/features/reports/charts/InteractionGraph.tsx:39-45` —
  removed local `const LEAF_CAP = 6;`; `data.groups.slice(0, 5)`
  → `slice(0, DISPLAY_CAPS.RELATIONS_GROUPS)` and
  `group.children.slice(0, LEAF_CAP)` →
  `slice(0, DISPLAY_CAPS.RELATIONS_LEAVES_PER_GROUP)`. Existing
  `+${overflow} more` leaf-meta merge (line 47-58) untouched.

**Cap rationale (recorded for posterity).**

+ `TIMELINE_EVENTS=800` / `EVENT_DENSITY_EVENTS=800` — midpoint of
  the tracker's 500-1000 band; comfortably above typical-report
  ranges (W14-2 ts-bound report fixtures sit in the low hundreds)
  yet ≪ the 2,803-event production scan so the indicator surfaces
  on real-world freezes. Even number for bucket math.
+ `RELATIONS_GROUPS=5` / `RELATIONS_LEAVES_PER_GROUP=6` — preserves
  the existing `InteractionGraph.tsx` `.slice(0, 5)` and
  `LEAF_CAP = 6` semantics. The InteractionGraph cap pattern was
  the W15-4 UX template; centralising the constants avoids drift
  between the layout (component-side) and the new groups-overflow
  indicator (caller-side in `InteractionsSection`).

**Post-filter ordering invariant.** Caps are applied **after**
the existing UI filter chain (`filterEvidenceEvents` →
`timelineEvents`) and after the chart-side
chronological/normalisation memos — never inside the DTO
adapter (`ui/src/lib/adapters/report.ts`). Preserves user filter
intent: a filter that narrows to 300 events shows all 300; the
cap only kicks in when the filtered total exceeds 800.

**Tests added.**

+ `ui/src/lib/displayCaps.test.ts` × **8** cases (pure helper):
  `applyDisplayCap` below cap returns input reference;
  boundary `count === cap` (truncated:false); above cap slice +
  overflow math; empty input; `cap=0` defensive path;
  `formatTruncationLabel` not-truncated returns empty string;
  truncated includes `+N`, locale-formatted totals, default noun
  and "filter to narrow"; `DISPLAY_CAPS` constants pin
  `RELATIONS_GROUPS=5` / `RELATIONS_LEAVES_PER_GROUP=6`
  value-preserving.
+ `ui/src/features/reports/charts/EventTimeline.test.tsx` × **7**
  cases (component, testing-library/react): empty events →
  empty-state branch, no indicator; below cap → all markers, no
  indicator; above cap → exactly cap markers; above cap →
  indicator with `+N more` / `first 800 of M`; boundary
  `count === cap` → indicator absent; cap applied after sort
  (rerender with two `selectedId` values to surface in-visible
  vs dropped-tail event labels); non-finite `relTimeS` filtered
  out before cap.
+ `ui/src/features/reports/charts/EventDensityStrip.test.tsx` ×
  **6** cases: empty events → placeholder buckets, no indicator;
  bucket count reflects post-cap maxT (outlier event at t=100s
  dropped); below cap → no truncation row; above cap →
  truncation row with `+N events truncated` and "density
  reflects first 800"; boundary `count === cap` → row absent;
  bucket click fires `onSelect` with first-event-in-bucket id.

Total: **21** new vitest cases (tracker target band 15-24).

**Verification.**

+ `cd ui && npm test` → **72/72 passed** (51 prior + 21 new).
+ `cd ui && npm run build` (tsc -b + vite) → clean.
+ `cd ui && npm run lint` → W15-4 files clean; one **pre-existing**
  error remains in `ui/src/features/settings/SettingsPage.tsx:472`
  (`react-hooks/set-state-in-effect`) from commit `65f741a`
  (`2026-05-09`) — out of W15-4 scope and not introduced by this
  iteration; the `make check-all` umbrella does not invoke
  `npm run lint`, so W15-1/W15-2/W15-3 close-outs also did not
  surface it. Candidate for W15-5 quick-fixes bundle or a
  dedicated UI-lint hygiene follow-up.
+ `make ui-types-check` (generated contract drift guard) → clean
  (`contracts.ts` not modified by W15-4).
+ `make ui-boundaries` → "UI feature boundaries are clean."
+ `make check-all` (lint + typecheck + security +
  ui-types-check + ui-boundaries + markdownlint + test) →
  **1857 passed / 10 skipped / 1 xfailed** (the W15-1 typing
  hotfix at `976dc96` unblocks the `make typecheck` gate that
  this run surfaced; pre-fix run reported a single
  `arg-type` error at `workflows/marketplace/router.py:342`).

**Production parity (regression guard).** Latest scan
`output/activation_report_ms-python.python-…-e260e3e13dab.json`
(2026-05-16 19:43; 2,803 `evidence_events`, 3,813
`evidence_links`, 2,543 `file_events`, 157 `network_events`,
70 `process_events`) compared against the W15-3 close baseline
scan
`output/activation_report_ms-python.python-…-774ec11fc136.json`
(2026-05-15 12:16; 2,804 / 3,801 / 2,541 / 163 / 63
respectively) shows **identical** verdict / quality / coverage
metrics across the entire 60-key top-level shape:
`runner_status=success`, `runner_exit_code=0`,
`target_extension_observed=true`, `trigger_plan_applied=true`,
`verification_gap=2`, `run_quality=low`,
`automation_health=degraded`, `signal_summary.level=needs_review`
with `score=28`, `risk_summary.total_signals=0`,
`coverage_summary` 7/5/6, `attempted=6`, `verified=4`. Event-
count deltas (≤ ±0.4%) are within natural run-to-run variance
(network jitter, FS timing, process scheduling); no W15-4-
attributable pipeline drift.

**Consciously excluded (defers to W15+).**

+ `evidence_links` cap — W15-4 caps event-class density (timeline +
  density bucket feed) and graph-group/leaf rendering, but
  `evidence_links` array (3,813 on the production scan) is not
  rendered as its own list; it feeds the
  `Inspector`/relations-graph-edges path. If a future audit flags
  edge-render freezes, that's a separate W15+ pull.
+ Backend report-side trim — explicitly out of scope per the
  W15-4 scope lock (W14-2 + W14-3 already addressed the
  backend-side caps; W15-4 is presentation-policy only).
+ Centralising the existing `LEAF_CAP=6` literal *behaviour* — the
  swap to `DISPLAY_CAPS.RELATIONS_LEAVES_PER_GROUP` is value-
  preserving; tightening the leaf cap further is a UX decision
  belonging to a future W15+ pull.
+ Generic UI-side lint hygiene sweep — the pre-existing
  `SettingsPage.tsx:472` `react-hooks/set-state-in-effect` error
  (commit `65f741a`, 2026-05-09) is real but unrelated to W15-4
  scope (event spread / timeline / relations). Track as a W15-5
  candidate or a dedicated quick fix.

### W15-5 — Quick fixes bundle: UI `/health` proxy + lifecycle `"for <id>"` regex — closed `2026-05-17` via `43d6438`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` +
`[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]`.

**Landing commit(s).** `43d6438` (single atomic commit covering
both I2 + I4 production code, the UI client URL migration, the
backend health-router module, and the behavioral tests for both
fixes). Follow-up `docs(W15-5): close` commit lands the tracker
narrative + §13 row + backlog audit trail per the
W15-1..W15-4 two-commit precedent (`c58c365` → `1bbb54d`,
`765cde7` → `c0c6066`, `3512a7c` → `74242c7`, `89e13e3` → `e1318eb`).

**Root cause (I2).** Pre-W15-5 the UI `apiClient.getHealth()` issued a
`fetch("/health", …)` call directly from
`ui/src/lib/api/client.ts:78`. All 12 other `apiClient` methods used
the `/api/*` prefix that nginx's `location /api/` block in
`ui/nginx/default.conf.template:13-20` proxies to the API container
(`${API_PROXY_PASS}` ≈ `http://api:8000`). The bare `/health` path
matched no nginx proxy block, so in production it fell through
`try_files $uri $uri/ /index.html` and either returned the SPA
fallback HTML or a `try_files`-resolved 404 — the UI healthcheck
silently broke whenever served from nginx. Docker healthchecks were
not load-bearing for the root `/health` HTTP path (`docker-compose.yml`
3 healthchecks use `pg_isready` for postgres / postgres_test and the
executor noVNC port 6080 — none HTTP-GET the API `/health` route);
external monitoring (if any) is the only remaining consumer, so the
legacy route is preserved as a back-compat surface.

**Root cause (I4).** Two of the six `_LIFECYCLE_MARKER_PATTERNS`
entries in
`executor/flows/playwright/runtime_capture/extension_host_log_parse.py`
used `\s*` (zero-or-more) between the verb and the next token and
`.*?(?P<id>[\w.\-]+)` (non-greedy any-char) to capture the id, with
no shape constraint on the id beyond `[\w.\-]+`. The pattern would
match log lines such as `activate returned 200` (capturing the
status code as the id) or `activate entered 12:34:56.789` (capturing
a timestamp). The four other patterns in the list were already
narrow — two enforced an `activate(<id>)` parenthesis form, and two
`register` patterns required an explicit `(?:for|by|from)` keyword
between the command/provider name and the id, so they were left
untouched. Post-W15-5 the two broad patterns require explicit
whitespace after the lifecycle verb (`\s+` instead of `\s*…\.*?`)
and constrain the id to the VS Code marketplace
`<publisher>.<name>` shape via `[\w-]+\.[\w.\-]+` (forces at least
one literal `.` and a non-dot leading character).

**Module locations.**

+ `appcore/api/health_router.py` (new, 20 LOC) —
  `router = APIRouter(prefix="/api", tags=["health"])`;
  `@router.get("/health")` returns
  `{"status": settings.api.HEALTH_STATUS, "service": settings.project.NAME}`
  — identical body to the legacy
  `workflows.extension_catalog.router.health_check`.
+ `main.py:18,82` — `from appcore.api.health_router import router as health_router`
  and `application.include_router(health_router)` appended after
  the existing four router includes; existing include of
  `extension_catalog_router` (which still owns root `/health`)
  untouched.
+ `ui/src/lib/api/client.ts:78` —
  `requestJson<...>("/health", { signal })` → `"/api/health"`;
  all 13 `apiClient.*` methods now uniformly use the `/api/*`
  prefix.
+ `ui/src/features/system/SystemPage.tsx:124,159` — display
  labels updated `/health` → `/api/health` for honesty (the
  Eyebrow chip and the inline `<code>` reference both surface
  the URL string to operators inspecting the system page).
+ `workflows/extension_catalog/router.py:46-49` — **untouched**
  per the additive-fix path; the root `/health` route remains
  for external-monitoring back-compat.
+ `executor/flows/playwright/runtime_capture/extension_host_log_parse.py:54-58,68-76` —
  two `_LIFECYCLE_MARKER_PATTERNS` regex entries tightened
  (see "Root cause (I4)" above for the verbatim before/after
  shape).
+ `executor/flows/playwright/runtime_capture/extension_host_log_parse.py:49-53,59-67,77-92` —
  **untouched**; narrow `(<id>)` parenthesis-form patterns and
  `register command|<Provider> for|by|from <id>` patterns kept
  as-is (already anchored by parenthesis or explicit keyword).

**Approach decisions (alternatives weighed).**

+ I2 path A (taken). Additive backend `/api/health` route via a
  new dedicated `appcore/api/health_router.py` module with
  `prefix="/api"`. Lowest blast radius — pure additive surface,
  no migration of any existing route; UI uniformity restored;
  legacy `/health` preserved.
+ I2 path B (rejected). Mount `extension_catalog_router` under
  `prefix="/api"`. Would have migrated ALL 10+ routes on the
  router (`/`, `/health`, `/searchExtension`,
  `/getExtensionsBaseInfo`, `/getExtensionsAllInfo`,
  `/createExtension`, `/deleteExtension`,
  `/getExtensionScripts`, `/getExtensionActivationEvents`,
  `/getExtensionCapabilities`, `/getExtensionContributesAll`,
  `/getExtensionContributesCommands`) under `/api/*`, breaking
  any external integration that hit the bare paths. Out-of-scope
  blast.
+ I2 path C (rejected). Add `location = /health` proxy block to
  nginx only; leave UI client unchanged. Preserves the
  `/api/*`-non-uniform UI surface and contradicts the W15-5
  scope intent ("UI tüm fetch'leri `/api/*` prefix'i üzerinden
  yapsın").
+ I2 path D (rejected). Add `@router.get("/api/health")` to
  `extension_catalog_router`. Domain-mixing — the extension
  catalog router should not own the health endpoint.
+ I4 path A (rejected). Require literal `for` keyword between
  the lifecycle verb and the id. Misses the
  `"activate entered <id>"` variant the source comment
  documents (line 54).
+ I4 path B (taken). `\s+` anchor + optional `(?:\s+for)?` +
  id constrained to `[\w-]+\.[\w.\-]+`. Both eliminates the
  unbounded `.*?` span AND constrains the id to a real
  `<publisher>.<name>` shape (peer-extension ids on the same
  log line also satisfy the publisher.name shape, but the
  `\s+` anchor now forces them to immediately follow the verb
  rather than appearing anywhere on the line).
+ I4 path C (rejected). Constrain only the id shape, keep
  `.*?`. Less invasive but leaves the unbounded `.*?` span;
  any peer-extension `<publisher>.<name>` token on the line
  would still match.

**Tests added.**

+ `tests/test_health.py` × **3** cases (extends existing
  `TestHealthCheck` class):
  + `test_legacy_health_endpoint` — root `/health` returns 200
    with the expected `status` + `service` body (pre-W15-5 the
    file did not cover this route at all even though it existed
    in `extension_catalog_router`).
  + `test_api_health_endpoint` — new `/api/health` returns 200
    with the same shape.
  + `test_api_health_matches_legacy_payload` — both routes
    return byte-identical JSON; pins the single-source-of-truth
    contract (any future divergence would surface here).
+ `ui/src/lib/api/client.test.ts` (new, 36 LOC) × **2** cases:
  + `getHealth() targets /api/health, not /health (nginx /api/*
    proxy)` — `vi.spyOn(global, "fetch")` + string-match against
    `/\/api\/health$/`, plus an explicit endsWith-`/health`-without-
    `/api/health` guard.
  + `getHealth() emits the bare /api/health path under the
    default (empty) base URL` — exact-string match
    `expect(urlString).toBe("/api/health")` (pins the empty-base-
    URL default branch of `getApiBaseUrl()` in
    `ui/src/lib/api/runtime.ts`).
+ `tests/executor/test_playwright_extension_host.py` × **9**
  cases (parametrize-style extension of the existing
  `test_parse_activations_from_output_emits_lifecycle_marker_types`
  test's scope):
  + Positive × **4** (`test_lifecycle_marker_tightened_positive_cases`,
    parametrized): `"activateFunction entered for ms-python.python"`
    → `(id=ms-python.python, marker=activate_fn_entry, ms=None)`;
    `"activate entered redhat.vscode-yaml"` →
    `(redhat.vscode-yaml, activate_fn_entry, None)`;
    `"activate returned for ms-python.python in 42 ms"` →
    `(ms-python.python, activate_fn_exit, 42)`;
    `"activate completed dbaeumer.vscode-eslint"` →
    `(dbaeumer.vscode-eslint, activate_fn_exit, None)`.
  + Negative × **5** (`test_lifecycle_marker_tightened_rejects_broad_matches`,
    parametrized — asserts the lifecycle markers list is empty):
    `"activate entered"` (no id at all — the pre-W15-5 loose
    regex returned no id either because `entered.*?(?P<id>…)`
    required a trailing token, but this case pins the contract);
    `"activate returned 200"` (id lacks dot — pre-W15-5 would
    have captured `200`); `"activate entered 12:34:56.789"`
    (timestamp shape — pre-W15-5 would have captured the
    timestamp tail); `"activating ms-python.python"` (wrong
    verb — `\s+` anchor was implicit pre-W15-5 too via
    `entered`/`returned`/`completed` literal but is reasserted);
    `"activated returned ms-python.python"` (wrong verb prefix
    `activated` — pre-W15-5 would have matched because the
    regex did not require word-boundary before `activate`; the
    tightened `\s+` anchor blocks this).

Total: **+14** new test cases (above the tracker forecast band
~6-10 — the parametrize matrices expanded the negative coverage
to defend against multiple specific log-noise shapes).

**Production diff.** `+20 LOC` new
`appcore/api/health_router.py`; `+2 LOC` `main.py` (import +
include); `+1 LOC / -1 LOC` `ui/src/lib/api/client.ts`
(`/health` → `/api/health`); `+2 LOC / -2 LOC`
`SystemPage.tsx` (two display labels); `+5 LOC / -3 LOC`
`extension_host_log_parse.py` (regex tightening with explanatory
comments). Net production diff `~+24 LOC`; tests `+13 LOC` in
`test_health.py`, `+36 LOC` new `client.test.ts`, `+70 LOC`
`test_playwright_extension_host.py`. Total `~+143 LOC`
production + tests.

**Verification.**

+ `pytest tests/test_health.py tests/executor/test_playwright_extension_host.py`
  **51 passed** (8 in `test_health.py` — 5 prior + 3 W15-5;
  43 in `test_playwright_extension_host.py` — 34 prior + 9
  W15-5).
+ `pytest tests/architecture/` collects **188 passed, 4
  deselected** — unchanged from the mid-iter hygiene baseline
  (186 → 188 was the `878da2c` doc-preamble consistency gate +
  README phase-pointer extension); W15-5 adds `+0` gates per
  the W14-6 "extend, do not duplicate" check (no existing
  `apiClient` URL prefix or `_LIFECYCLE_MARKER_PATTERNS` shape
  gate to extend; new gates deferred to W15-7 close-out hygiene
  per the W15-5 plan).
+ `make test-security` **215 passed, 35 warnings** — unchanged
  from W13 / W14 / W15-1..W15-4 baseline; no security surface
  touched.
+ `cd ui && npm test -- --run` — **74 passed across 18 files**
  (72 prior + 2 new in `client.test.ts`).
+ `cd ui && npx tsc --noEmit` — clean (no TypeScript errors).
+ `make typecheck` — **Success: no issues found in 356 source
  files** (Python mypy; W15-5 touched 3 source files —
  `main.py`, `appcore/api/health_router.py`, and
  `extension_host_log_parse.py` — all clean).
+ `ruff check appcore/api/health_router.py main.py
  executor/flows/playwright/runtime_capture/extension_host_log_parse.py
  tests/test_health.py tests/executor/test_playwright_extension_host.py`
  — `All checks passed!`.

**Consciously excluded (defers to W16+ or W15-7 close-out
hygiene).**

+ Sweep of all `apiClient` methods for the `/api/*` prefix —
  only `getHealth` had the bare path; the other 12 methods were
  already correct, so a generic AST gate is deferred to W15-7
  close-out hygiene if useful (low value; the broken case is
  fixed and the pattern is socially obvious — every method goes
  through `requestJson(path, …)` with a string-literal path that
  shows up in code review).
+ Removal of the legacy root `/health` route on
  `extension_catalog_router` — kept for external-monitoring
  back-compat; removal would need a deprecation window and an
  inventory of consumers (Docker healthchecks not affected per
  the verification above, but external monitoring may exist).
+ Nginx config change — `location /api/` already proxies
  `/api/health` correctly; no nginx edit needed. A separate
  `location = /health` proxy block (path C) was explicitly
  rejected in favor of additive backend.
+ Tightening of the `register command` / `register <Provider>`
  patterns at line 77-92 — already anchored by explicit
  `(?:for|by|from)` keyword; W15-5 scoped to the
  `activate entered` / `activate returned|completed` entry/exit
  patterns only.
+ Stricter VS Code marketplace id validator (e.g.
  `[a-z0-9][a-z0-9-]*\.[a-z0-9][a-z0-9.-]*`) — W15-5 enforces
  only the `<publisher>.<name>` dot-bearing shape; full
  marketplace naming rules belong to a generic id-validator
  W16+ candidate if a future audit flags it.
+ Pre-existing `SettingsPage.tsx:472`
  `react-hooks/set-state-in-effect` lint error (flagged at
  W15-4 close-out as a W15-5 candidate) — W15-5 scope locked
  to I2 + I4 quick fixes only; the SettingsPage lint error
  remains for a dedicated UI-lint hygiene follow-up. Adding it
  here would have widened the close-out beyond the planned
  bundle.

**Risk profile (post-landing).** **Low.** Both fixes are
additive or scope-tightening; neither touches DB migration,
ADR security posture, executor sandbox boundary, or the
contracts surface. The I4 false-negative risk (a legacy
single-token extension id — e.g. a built-in VS Code extension
without the `<publisher>.<name>` shape — slipping past the
tightened lifecycle pattern) is mitigated by the existing
`_ACTIVATION_PATTERNS` family (line 15-39), which still uses
the loose `[\w.\-]+` id capture and remains the primary
activation-detection path; `_LIFECYCLE_MARKER_PATTERNS` only
enriches activation entries with a `marker_type` field, so a
miss degrades enrichment quality rather than dropping the
activation record. Post-rebuild fresh-scan inspection should
confirm the `marker_type`-bearing entry count stays within the
established natural-jitter band against the W15-4
post-rebuild baseline scan.

### W15-6 — Unauthenticated catalog endpoints posture (ADR 0011) — closed `2026-05-17` via `be52520`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`.

**Landing commit(s).** Proposed at `e41722e`
(`docs(W15-6): ADR 0011 — unauthenticated catalog endpoints
posture (Proposed)`); Accepted and implemented at `be52520`
(`feat+test(W15-6): catalog posture docstring + arch gate (ADR
0011)`). Follow-up `docs(W15-6): close` commit lands the tracker
narrative, §13 row, backlog audit trail close, and the canonical
preamble refresh per the W15-3/W15-4/W15-5 close-docs precedent.

**Posture decision.** **Option A** — catalog endpoints remain
unauthenticated under three preconditions cited in ADR 0011:

1. Single-host appliance scope (ADR 0001) is unchanged.
2. Loopback bind default (ADR 0007 §1) is unchanged.
3. LAN exposure (`EXTRACE_ALLOW_LAN=1` opt-in) requires
   operator-side hardening per
   `documents/runbooks/lan-exposure.md`.

The Codex Cloud audit `2026-05-10` raised the posture question
under `U10/U11 unauth-catalog-endpoints`. ADR 0002 §5 already
sets the single-operator boundary; §4 row 102 already routes
operator-host network exposure through ADR 0007's
`EXTRACE_ALLOW_LAN` single audited opt-in. The UI does not call
catalog endpoints (`ui/src/lib/api/client.ts` audit at HEAD
`4999cab` shows only `/api/activations/*`, `/api/marketplace/*`,
`/api/settings/*`, and `/api/health` are reachable from the UI).
Adding per-request auth would defend against an adversary class
the threat model does not name; the cost is real, the benefit
is conjectural. Forward path to Option B (per-request HMAC
marker auth) preserved as a follow-on — ADR 0011 Follow-On
section enumerates the triggers (ADR 0001 amendment, ADR 0002
§1 adversary class addition, CDP `debug` default-on).

**Module locations.**

- ADR: [`documents/adrs/0011-unauthenticated-catalog-endpoints-posture.md`](../adrs/0011-unauthenticated-catalog-endpoints-posture.md).
- Code anchor: [`workflows/extension_catalog/router.py`](../../workflows/extension_catalog/router.py)
  module docstring (lines 1-10) + inline comment at the
  `router = APIRouter(tags=["core"])` construction site (lines 33-37).
- Architecture gate: [`tests/architecture/test_catalog_endpoint_posture.py`](../../tests/architecture/test_catalog_endpoint_posture.py)
  (new file).

**Gate invariants (three AST tests).**

1. `test_catalog_router_module_cites_adr_0011` — module docstring
   contains the substring `ADR 0011`. Sessiz doc decay'i
   engeller.
2. `test_catalog_router_has_no_auth_dependency` — AST walk of the
   `APIRouter(...)` `ast.Call` rejects any `dependencies=[...]`
   kwarg whose list/tuple element callable names match
   `^(auth|require_|verify_|hmac_|marker_).*`. Option B'ye sessiz
   drift'i engeller.
3. `test_catalog_router_endpoint_count_locked` — `@router.<verb>`
   decorator count is locked at **12** (11 catalog endpoints +
   `/` root). Yeni endpoint eklemek bu gate'i kırar → ADR 0011
   amendment review zorunluluğu.

**Tests.**

- `pytest tests/architecture/test_catalog_endpoint_posture.py -v`
  → 3 passed (3 AST test functions in the new gate file).
- `pytest tests/architecture/ -q` → 191 passed / 4 deselected
  (W15-5 baseline 188 + 3 new functions from the gate file).
- `pytest tests/workflows/extension_catalog/test_router.py
  tests/test_health.py -q` → 42 passed (no behavioral
  regression on the catalog or `/health` surfaces).
- `make test-security` → 215 passed (unchanged from W15-5).
- `make markdownlint` → clean (ADR + tracker + backlog).
- `pytest tests/architecture/test_adr_code_fence_language.py -v`
  → 1 passed (ADR markdown discipline).
- `pytest tests/architecture/test_doc_preamble_consistency.py -v`
  → 1 passed (canonical preambles agree on `W15 active`).

**Gate accounting.** `+1 gate file` per the W14-6 "extend, do
not duplicate" convention; `+3` test functions per the pytest
function count. Tracker target deltas table records both.

**Tracker drift fix.** Tracker text referenced
`documents/decision-records/0011-...` for the ADR path; actual
repo directory is `documents/adrs/` (ADRs 0001..0010 all
located there). Drift noted in the W15-6 §2.1 close evidence;
ADR landed at the correct path.

**Threat model amendment.** ADR 0002 is **not** amended. Option
A re-uses the existing §4 row 102 (operator-host network
interfaces, ADR 0007) and §5 (analyst operating environment)
assumptions without restating; ADR 0011 cites them as
load-bearing prerequisites in its `Related:` header and
Decision section.

**Bilinçli hariç (W16+ aday).** Per-request HTTP HMAC marker
auth (Option B) is the natural follow-on if the threat model
expands. ADR 0011 Follow-On section explicitly states this is
an adaptation, not a copy, of the W13-1 launch-scoped HMAC —
HTTP-request auth requires header signing, time-window nonce,
replay protection, and a secret-distribution channel for
non-UI clients. Reverse-proxy auth at the
`EXTRACE_ALLOW_LAN=1` boundary remains the canonical control
surface per `documents/runbooks/lan-exposure.md`; per-route
HMAC is the defense-in-depth complement, not a replacement.

**Risk profile (post-landing).** **Low.** Zero behavioral code
change — module docstring + inline comment + new test file.
No DB schema, no migration, no executor sandbox boundary, no
contracts surface, no UI consumer impact (UI does not call
catalog endpoints). Posture is now locked by code + gate +
ADR; future drift surfaces at PR time, not at audit time.

W15 kapanır şu koşullar sağlandığında:

+ W15-1..W15-7 kapanır ya da deferral rasyoneli ile W16'ya taşınır.
+ W15 tracker final close evidence + current test counts tutar.
+ `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `active-work/README.md`,
  ve ilgili lane docs aynı active/closed state'i gösterir.
+ Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
+ `week15 → main` close-out PR W12 PR #18 / W13 PR #20 / W14 PR #21
  cut-off pattern'ini izler.
+ Close-out hygiene pass (W14 paterni): Ruff lint, UI contract sync,
  markdown formatting, doc truth-state alignment, (varsa) yeni
  regression gate'ler. W15-7 doc preamble refresh'i bu pass'in
  parçası olarak finalize.
