# Executor: Playwright UI Automation & Honeypot Environment

`Last Updated: 2026-02-09` | `Status: Active Development`

---

## Overview

Executor container'i icerisinde VS Code GUI'sini Playwright CDP (Chrome DevTools Protocol) uzerinden otomasyon ile kontrol eden modul sistemi. Her modul tek sorumluluk tasir, fonksiyon bazli (class yok), stateless ve composable.

Ek olarak, zararli extension'larin hedef alabilecegi gercekci bir **honeypot gelistirici ortami** container basladiginda otomatik kurulur.

---

## Dosya Yapisi

```
executor/
├── Dockerfile                # Ubuntu 22.04 + VS Code + monitoring tools
├── start.sh                  # Container entrypoint (Xvfb, VNC, VS Code, honeypot)
├── requirements.txt          # Python dependencies (playwright)
├── __init__.py
└── playwright/
    ├── __init__.py            # Package docstring
    ├── keyboard.py            # VS Code kisayol sabitleri (tek kaynak)
    ├── vscode.py              # CDP baglanti, ready bekleme
    ├── commands.py            # Command Palette islemleri
    ├── editor.py              # Editor: dosya ac/kaydet/kapat/yaz
    ├── sidebar.py             # Activity Bar ve sidebar view'lari
    ├── terminal.py            # Entegre terminal
    ├── panel.py               # Alt panel: problems, output, debug console
    ├── workspace.py           # Filesystem: honeypot ortami + dosya islemleri
    └── entrypoint.py          # Demo script (tum helper'lari kullanan ornek)
```

---

## Container Baslangic Akisi

`start.sh` calistiginda sirayla:

```
1. Xvfb :99 (1920x1080x24)     -> Sanal ekran
2. Openbox                       -> Pencere yoneticisi
3. x11vnc (port 5900)           -> VNC sunucu
4. workspace.py                  -> Honeypot ortami kurulumu
5. VS Code settings.json         -> Trust/telemetry devre disi
6. VS Code /workspace            -> GUI baslatilir (CDP port 9222)
7. noVNC (port 6080)            -> Tarayici erisimi
```

### VS Code Oto-Konfigurasyon

`start.sh`, VS Code baslamadan once su ayarlari yazar:

```json
{
  "security.workspace.trust.enabled": false,
  "workbench.startupEditor": "none",
  "telemetry.telemetryLevel": "off",
  "update.mode": "none"
}
```

Bu sayede:
- **Workspace Trust dialogu** cikmaz
- **Welcome tab** acilmaz
- **Telemetry** kapalir
- **Auto-update** devre disidir

VS Code, `/workspace` klasorunu direkt acar — manuel secim gerekmez.

---

## Modul Detaylari

### keyboard.py — Kisayol Sabitleri

Tum VS Code keyboard shortcut'lari tek yerde tanimlidir. Diger moduller bu sabitleri import eder. VS Code bir kisayol degistirirse sadece bu dosya guncellenir.

```python
# Ornekler
COMMAND_PALETTE = "Control+Shift+KeyP"
QUICK_OPEN      = "Control+KeyP"
NEW_FILE        = "Control+KeyN"
SAVE_FILE       = "Control+KeyS"
TOGGLE_TERMINAL = "Control+Backquote"
FOCUS_EXPLORER  = "Control+Shift+KeyE"
```

**Tam liste:** Command Palette, Quick Open, Editor (new/save/close), Sidebar (explorer/search/scm/debug/extensions), Panel, Terminal, Navigation.

---

### vscode.py — CDP Baglanti

VS Code'a Chrome DevTools Protocol uzerinden baglanir.

| Fonksiyon | Aciklama |
|-----------|----------|
| `connect(playwright)` | CDP uzerinden baglanir, `(browser, page)` doner |
| `wait_until_ready(page, timeout_ms)` | `.monaco-workbench` gorunene kadar bekler |
| `disconnect(browser)` | CDP baglantiyi kapatir |

```python
from playwright.sync_api import sync_playwright
import vscode

with sync_playwright() as pw:
    browser, page = vscode.connect(pw)
    vscode.wait_until_ready(page)
    # ... islemler ...
    vscode.disconnect(browser)
```

**CDP URL:** `http://localhost:9222` (env: `EXECUTOR_CDP_PORT`)

---

### commands.py — Command Palette

Command Palette ve Quick Open islemleri. **Her fonksiyon Enter basar ve widget'in kapanmasini bekler.**

| Fonksiyon | Aciklama |
|-----------|----------|
| `open_command_palette(page)` | Palette'i acar, gorunur olmasini bekler |
| `run_command(page, command_text)` | Palette'i acar, komutu yazar, Enter basar, **kapanmasini bekler** |
| `quick_open(page, query)` | Ctrl+P acar, sorguyu yazar, Enter basar, **kapanmasini bekler** |

**Onemli detay:** VS Code `.quick-input-widget`'i DOM'dan kaldirmaz, `display: none` yapar. Bu yuzden widget'in kapandigi ozel CSS selektoru ile kontrol edilir:

```python
_QUICK_INPUT_VISIBLE = ".quick-input-widget:not([style*='display: none'])"
```

**Kapsar:** `onCommand:*` activation event'lari.

---

### editor.py — Editor Islemleri

Dosya acma, yazma, kaydetme, kapatma.

| Fonksiyon | Aciklama |
|-----------|----------|
| `new_untitled_file(page)` | Yeni bos tab acar (Ctrl+N) |
| `save_file(page)` | Mevcut dosyayi kaydeder (Ctrl+S) |
| `save_file_as(page, filename)` | Save-As dialog'u ile kaydeder (**xdotool**) |
| `close_active_editor(page)` | Aktif tab'i kapatir (Ctrl+W) |
| `type_in_editor(page, text)` | Editore yazi yazar |
| `open_file_by_name(page, filename)` | Quick Open ile dosya acar |
| `close_all_editors(page)` | Tum tab'lari kapatir (Command Palette) |

**Native Dialog Sorunu:** `save_file_as` fonksiyonu `Ctrl+Shift+S` ile GTK native file dialog acar. Bu dialog Playwright'in DOM'unda degildir — Chromium web sayfasinin disindadir. Bu yuzden `xdotool` kullanilir:

```python
subprocess.run(["xdotool", "key", "ctrl+a"], check=True)      # Mevcut adı sec
subprocess.run(["xdotool", "type", "--delay", "30", filename]) # Yeni adi yaz
subprocess.run(["xdotool", "key", "Return"], check=True)       # Kaydet
```

**Kapsar:** `onLanguage:*`, `onCustomEditor:*` activation event'lari.

---

### sidebar.py — Sidebar & Activity Bar

Sol sidebar view'larini acma/kapama.

| Fonksiyon | Aciklama |
|-----------|----------|
| `toggle_sidebar(page)` | Sidebar goster/gizle (Ctrl+B) |
| `open_explorer(page)` | Explorer view (Ctrl+Shift+E) |
| `open_search(page)` | Search view (Ctrl+Shift+F) |
| `open_source_control(page)` | Source Control (Ctrl+Shift+G) |
| `open_debug(page)` | Run & Debug (Ctrl+Shift+D) |
| `open_extensions_view(page)` | Extensions (Ctrl+Shift+X) |
| `open_view_by_command(page, view_name)` | Command Palette ile herhangi bir view |

**Kapsar:** `onView:*` activation event'lari. `open_view_by_command` custom `viewContainers` icin kullanilir.

---

### terminal.py — Entegre Terminal

| Fonksiyon | Aciklama |
|-----------|----------|
| `toggle_terminal(page)` | Terminal paneli goster/gizle |
| `new_terminal(page)` | Yeni terminal olustur (Command Palette) |
| `type_in_terminal(page, text, press_enter=True)` | Terminal'e yaz, varsayilan olarak Enter basar |

`press_enter=True` varsayilanidir — komut yazildiktan sonra otomatik calistirilir.

---

### panel.py — Alt Panel

| Fonksiyon | Aciklama |
|-----------|----------|
| `toggle_panel(page)` | Alt panel goster/gizle (Ctrl+J) |
| `open_problems(page)` | Problems tab'i (Command Palette) |
| `open_output(page)` | Output tab'i |
| `open_debug_console(page)` | Debug Console tab'i |

---

### workspace.py — Filesystem & Honeypot Ortami

Iki sorumlulugu vardir:

1. **Genel dosya islemleri** — `create_workspace_file`, `create_workspace_dir`, `create_language_file`, `create_workspace_structure`, `clean_workspace`
2. **Honeypot gelistirici ortami** — `setup_dev_environment()`

**Playwright'a bagimli degildir** — saf `pathlib` ve `shutil` kullanir.

**Container basladiginda `start.sh` tarafindan otomatik calistirilir.**

```bash
# start.sh icinde, VS Code'dan ONCE:
python3 /home/executor/playwright/workspace.py
```

---

## Honeypot Gelistirici Ortami

`setup_dev_environment()` fonksiyonu iki lokasyona dosyalar olusturur:

### /workspace/ (Proje Dizini)

VS Code bu klasoru otomatik acar. Extension'larin tarayacagi proje dosyalari:

| Dosya/Klasor | Icerik |
|-------------|--------|
| `.env` | DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, STRIPE_SECRET_KEY, AWS keys, SENTRY_DSN |
| `.env.production` | Production DB URL, API key |
| `.env.local` | Local dev credentials |
| `.git/config` | GitHub remote URL (SSH) |
| `src/app.py` | Flask uygulamasi |
| `src/config.py` | `os.environ.get()` ile credential okuma |
| `src/database.py` | Hardcoded DB connection string |
| `src/auth.py` | JWT secret, token islemleri |
| `src/payments.py` | Stripe API key |
| `src/storage.py` | AWS S3 boto3 client |
| `frontend/.env` | React app env (Stripe publishable key, Sentry DSN) |
| `frontend/package.json` | Node.js dependencies |
| `docker-compose.yml` | DB/Redis sifreleri acik text |
| `credentials/gcp-service-account.json` | GCP service account (fake private key) |
| `credentials/firebase-admin-sdk.json` | Firebase admin SDK |
| `infra/terraform.tfvars` | DB sifresi, Redis sifresi, API secret |
| `infra/main.tf` | AWS RDS tanimlamasi |
| `scripts/deploy.sh` | Docker login tokeni, SSH komutu |
| `scripts/seed.py` | Hardcoded DB sifresi |
| `scripts/backup.sh` | pg_dump connection string |
| `.wallet/keystore.json` | Ethereum wallet (fake) |
| `alembic/env.py` | SQLAlchemy URL |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Prod container |
| `README.md` | Proje tanitimi |

### /home/executor/ (Kullanici Profili)

Extension'larin `$HOME` dizinini tarayarak erisebilecegi dosyalar:

| Dosya | Icerik |
|-------|--------|
| `.ssh/id_rsa` | OpenSSH private key (chmod 600) |
| `.ssh/id_rsa.pub` | Public key |
| `.ssh/config` | GitHub + production server |
| `.ssh/known_hosts` | GitHub fingerprint |
| `.aws/credentials` | AWS access key + secret (default & production profil) |
| `.aws/config` | Region ayarlari |
| `.kube/config` | Kubernetes cluster token |
| `.docker/config.json` | Docker registry auth (ghcr.io, private registry) |
| `.config/gcloud/application_default_credentials.json` | GCP OAuth refresh token |
| `.npmrc` | NPM ve GitHub Packages auth token |
| `.gitconfig` | Git kullanici bilgileri |
| `.git-credentials` | GitHub PAT (plaintext) |
| `.bash_history` | SSH, docker login, kubectl, aws, curl + API key komutlari |
| `.python_history` | boto3, os.environ erisimleri |

### Tasarim Prensipleri

- Tum credential'lar **fake ama format olarak dogru** — gercek regex pattern'larina uyar
- AWS key'ler `AKIA...` prefixi ile baslar (gercek format)
- SSH key'ler dogru permission'lara sahiptir (600/700)
- `.bash_history` gercekci komutlar icerir
- Dosya yapisi tipik bir startup backend projesini yansitir

---

## Import Stratejisi

`executor/playwright/` dizini pip'teki `playwright` paketiyle isim catismasi yaratir. Cozum:

1. **Helper moduller** (`commands.py`, `editor.py`, vb.) birbirlerini **dogrudan import** eder: `import keyboard`, `from commands import run_command`
2. **pip `playwright`** paketi normal calismaya devam eder: `from playwright.sync_api import Page`
3. **`entrypoint.py`** kendi dizinini `sys.path`'e ekleyerek bu yapiyi bootstrap eder:

```python
_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)
```

4. **`workspace.py`** Playwright'a hic bagimli degildir — `start.sh` tarafindan dogrudan `python3 /path/to/workspace.py` olarak calistirilir.

---

## Activation Event Kapsam Tablosu

| Activation Event | Tetikleyen Modul | Yontem |
|-----------------|------------------|--------|
| `*` | — | VS Code startup |
| `onStartupFinished` | — | VS Code startup |
| `onLanguage:*` | `workspace.py` + `editor.py` | Dile uygun dosya olustur + ac |
| `onCommand:*` | `commands.py` | Command Palette ile komut calistir |
| `workspaceContains:*` | `workspace.py` | Container baslarken dosya olustur |
| `onView:*` | `sidebar.py` | Klavye kisayolu veya Command Palette |
| `onCustomEditor:*` | `editor.py` | Ilgili dosya tipini ac |
| `onWebviewPanel:*` | `commands.py` | Ilgili komutu calistir |

---

## Kullanim

### Container Baslatma
```bash
make executor-build     # Image olustur
make executor-up        # Container baslat (honeypot + VS Code otomatik)
```

### Playwright Demo Calistirma
```bash
make executor-playwright   # entrypoint.py calistirir
```

### noVNC ile Gozlem
```
http://localhost:6080/vnc.html
```

### Container Shell
```bash
make executor-shell
```

---

## Bilinen Kisitlamalar

| Kisitlama | Aciklama | Workaround |
|-----------|----------|------------|
| Native dialog'lar | GTK file picker Playwright DOM'unda degil | `xdotool` ile etkilesim |
| Paket isim catismasi | `playwright/` dizini pip paketi ile catisir | `sys.path` bootstrap + dogrudan import |
| Quick Input widget | VS Code DOM'dan kaldirmaz, `display:none` yapar | Ozel CSS selektoru ile kontrol |

---

## Sonraki Adimlar

- [ ] Extension yukleme/kaldirma otomasyonu (`code --install-extension`)
- [ ] Monitoring entegrasyonu (tcpdump, inotifywait, strace)
- [ ] Activation event'a gore otomatik trigger secimi
- [ ] Analiz sonuclarini DB'ye kaydetme
- [ ] Persona-bazli simulasyon (Phase 2)
