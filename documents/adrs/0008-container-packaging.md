# ADR 0008: Container Packaging — Package-Mode Canonical Invocation

- Status: Proposed
- Date: 2026-04-30
- Related: ADR 0001 (Single-Host Appliance), ADR 0005 (Packages Charter), ADR 0007 (Local Network Binding)

## Context

ExTrace executor entrypoint script'leri iki farklı import topolojisinde
çalışıyor:

1. **Top-level (flat) mode** — production runtime: `docker exec ... python3
   /home/executor/flows/playwright/entrypoint.py`. `entrypoint.py:16-18`
   `sys.path.insert(0, _pkg_dir)` ile script'i çalıştırırken kardeş
   modülleri (`automation`, `commands`, `editor`, `monitor` …) flat
   namespace'e yerleştirir. `import automation`, `from monitor import
   ExtensionMonitor` flat name ile çözülür.
2. **Package mode** — host-side test invocation: `python -m
   executor.flows.playwright.entrypoint`. Modüller dotted form
   (`from .monitor import ExtensionMonitor`) ile çözülür.

Aynı kod tabanı bu çift sözleşmeyi 18 dosyada `try: from .X import Y;
except ImportError: from X import Y` blokları ve 5 runtime
`sys.path.insert` çağrısı ile destekliyor (`signal_policy.py:33`,
`entrypoint.py:18`, `reload_vscode.py:19`, `triggers.py:27`,
`report_builder.py:17`). Her yeni dosya iki sürüm import bloğu taşımak
zorunda.

Bu drift'in birkaç yan etkisi:

- **ADR 0005 §3 ihlali** — `executor/flows/playwright/signal_policy.py`
  detection signal policy içerir (severity rollup, correlative evaluation,
  confidence tier'ları), bu kod framework-agnostic `packages/` altına
  ait. Ancak `executor/`'dan `packages/`'a relocation, paket-mode import
  sözleşmesi olmadan yapılırsa flat-mode çalışmaz hale getirir.
- **W10/W11 modülerleştirme borç biriktirir** — `monitor_lifecycle.py`
  split (W11) ve `registry.py` 4-way split (W10) sırasında her yeni dosya
  dual-import bloğu taşımak zorundadır.
- **`pkill -f` cleanup file-path'e bağımlı** — `executor/host.py:201,
  211` cleanup çağrıları `settings.executor.RELOAD_SCRIPT_PATH` /
  `ENTRYPOINT_PATH` literal'ları üzerinden process command-line'ı arıyor.
  File-path string'ine bağımlılık trafonu tarafsız değil; container yolu
  rename edildiğinde silently break eder.
- **Settings env override yüzeyi** — `EXECUTOR_ENTRYPOINT_PATH` ve
  benzerleri eski deployment artefaktları olarak yaşar; herhangi bir
  override yanlış path'e işaret ederse failure mode runtime'a düşer.

## Decision

Operatorün container'a eriştiği invocation tek bir mode'a indirilir;
script-as-file yaklaşımı reddedilir.

### 1. Canonical invocation: package-mode

Production'da çağrılan tüm executor entrypoint script'leri `python -m
<dotted.module>` argv-form'unda invoke edilir. File-path invocation
(`python /home/.../X.py`) reddedilir ve regression test ile kilitlenir.

Etkilenen 4 entrypoint:

| Module | Sahip |
|---|---|
| `executor.flows.playwright.entrypoint` | automation (host.py) |
| `executor.flows.playwright.reload_vscode` | reload (host.py) |
| `executor.flows.playwright.reset_state` | reset (host.py) |
| `executor.flows.playwright.workspace` | boot-time honeypot (start.sh) |

### 2. Container layout: regular package

`Dockerfile` aşağıdaki dosyaları yaratır ve `PYTHONPATH`'i set eder:

```dockerfile
RUN touch /home/executor/__init__.py /home/executor/flows/__init__.py \
    && chown executor:executor /home/executor/__init__.py /home/executor/flows/__init__.py
ENV PYTHONPATH=/home
```

Bu, `executor.flows.playwright.X` dotted import'larını PEP 420 namespace
package'tan regular package'a yükseltir; niyet açık ve IDE/static-analysis
tutarlı.

Host repo'da da `executor/flows/__init__.py` boş marker dosyası eklenir
ki host-side test koşumu container ile birebir aynı paket layout'u
gösterirsin.

### 3. host.py + start.sh argv pivot

- `executor/host.py:236, 252, 290-298` — `[PYTHON3_PATH, "-m",
  settings.executor.<X>_MODULE]` formuna geçer.
- `executor/host.py:201, 211` — `pkill -f` pattern olarak dotted module
  name kullanılır (örn `executor.flows.playwright.entrypoint`); bkz §6.
- `executor/container/start.sh:82` — `python3 -m
  executor.flows.playwright.workspace` formuna geçer; eski
  `${PLAYWRIGHT_FLOW_DIR}/workspace.py` dispatch silinir.
- `Makefile` `exec-run`, `sim-all`, `sim-target`, `sim-demo`, `sim-list`,
  `sim-run` hedefleri argv-form'a geçer.

### 4. Settings clean-cut migration

`ExecutorSettings` (`appcore/api/config.py:170-219` ve
`executor/config.py:60-107`):

- Yeni alanlar: `ENTRYPOINT_MODULE`, `RELOAD_SCRIPT_MODULE`,
  `RESET_SCRIPT_MODULE` (string, dotted module name).
- Eski alanlar `ENTRYPOINT_PATH`, `RELOAD_SCRIPT_PATH`,
  `RESET_SCRIPT_PATH` ve env override'ları (`EXECUTOR_ENTRYPOINT_PATH`
  vb.) **silinir** — deprecation alias bırakılmaz. Eski env değişkeni
  ayarlı bir deployment varsa, `extra="ignore"` (Pydantic) sayesinde
  process boot başarılı olur ama değer hiçbir yerde okunmaz.

### 5. Architecture regression test

`tests/architecture/test_container_entrypoint.py` (W9-5):

- Positive: `docker exec automation_executor python -c "import
  executor.flows.playwright.entrypoint"` → `RC=0`.
- Negative: `docker exec automation_executor python
  /home/executor/flows/playwright/entrypoint.py` → `RC≠0` (PYTHONPATH +
  paket layout flat-mode invocation'ı `__main__` guard veya import
  failure ile reddetmeli).
- `@pytest.mark.smoke`; docker yoksa skip; pre-push hook smoke lane'ine
  fold.

### 6. `pkill -f` pattern: dotted module name uniqueness invariant

`executor/host.py` cleanup çağrıları `pkill -f` pattern olarak doğrudan
dotted module name'i kullanır:

```python
[PKILL_PATH, "-f", settings.executor.RELOAD_SCRIPT_MODULE]
# pattern: "executor.flows.playwright.reload_vscode"
```

Bu pattern güvenliği aşağıdaki invariant'a dayanır:

> **Invariant:** Container içinde bir process'in command-line argümanları
> arasında bir entrypoint module'ünün dotted name'i (örn
> `executor.flows.playwright.entrypoint`) sadece o module'ün kendisi
> `python -m` formuyla başlatıldığında geçer. Aynı string başka bir
> process'in argv'sinde geçemez çünkü:
>
> - Module name Python paketleme konvansiyonuna göre (PEP 423) global
>   namespace'te benzersizdir.
> - Container'da çalışan diğer process'ler (Xvfb, x11vnc, VS Code,
>   tcpdump …) Python module yolu argümanı kabul etmez.
> - Harness extension'ı VS Code subprocess olarak yüklenir, command-line
>   argv'si module name içermez.

Bu invariant'ı korumak için yeni bir entrypoint module eklendiğinde
**dotted name ortak bir prefix taşımalı** (`executor.flows.playwright.*`
veya gelecekte `executor.flows.<other>.*`); generic isimlerden
(`entrypoint`, `runner`, `main`) kaçınılır.

Test koruma: `tests/architecture/test_container_entrypoint.py` Negative
case'in altına ek bir assertion ekler — `pgrep -f
executor.flows.playwright.entrypoint` boş container state'inde 0 hit
döner (false-positive baseline doğrulaması).

## Consequences

### Positive

- Tek import topolojisi → review yorgunluğu, drift riski sıfır.
- ADR 0005 framework-agnostic kuralına uyum yolu açılır
  (`signal_policy.py` paket altına relocation W9-2'de güvenli).
- W10-W12 yeni modülleri tek import bloğu taşır.
- `pkill` cleanup'ı dotted module name ile daha sağlam — file-path
  drift'inden bağımsız.
- Settings yüzeyi sadeleşir; eski env var'lar silinince deployment
  ergonomi netleşir.

### Negative

- Eski `EXECUTOR_*_PATH` env var'larını set eden deployment'lar bir
  uyarı görmeden deprecated değeri yok sayar (Pydantic `extra="ignore"`
  silently absorbe eder). `.env.example` ve runbook bu değişiklikten
  bahseder.
- Container'da iki yeni `__init__.py` dosyası ve `PYTHONPATH=/home` env
  set'i eklenir; minimal artefakt ama image build'inde hash değişir.
- `pkill -f` pattern'inin güvenliği §6 invariant'ına bağlıdır;
  invariant'ı koruyacak naming convention discipline gerekir.

### Follow-On

- W9-1 commit'inde implement edilir (`feat/w9-executor-detection-boundary`
  umbrella).
- W9-2'de `signal_policy.py` `packages/analysis_engine/signals/policy.py`
  altına minimum-invaziv relocation.
- W9-3'te 18 dosyada `except ImportError` fallback elimine edilir.
- W9-4'te runtime tree'deki son 5 `sys.path.insert` kaldırılır.
- W9-5'te container import-mode regression test eklenir.
- `documents/executor/playwright-flow.md`, `documents/EXECUTOR_PLAYWRIGHT.md`,
  `documents/architecture/data-flow.md`, `README.md` ve runbook'lardaki
  file-path referansları W9 closure pas'ında module-name formuna
  güncellenir.

## Implementation

W9-1 implementation closure'da bu bölüm doldurulacak; ADR 0007 deseni
(`Implementation` bölümü Status `Accepted` flip ile birlikte yazılır).
