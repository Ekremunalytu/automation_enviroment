import os
import time

from playwright.sync_api import sync_playwright

CDP_URL = f"http://localhost:{os.environ.get('EXECUTOR_CDP_PORT', '9222')}"


def main():
    with sync_playwright() as p:
        print(f"[*] VS Code'a baglaniliyor ({CDP_URL})...")
        browser = p.chromium.connect_over_cdp(CDP_URL)

        # VS Code'un ana penceresi
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"[+] Baglanti kuruldu - sayfa: {page.title()}")

        # VS Code UI tam yuklenene kadar bekle
        time.sleep(2)

        # Command Palette ac (Ctrl+Shift+P)
        print("[*] Command Palette aciliyor...")
        page.keyboard.press("Control+Shift+KeyP")
        time.sleep(1)

        # Terminal ac komutu yaz
        page.keyboard.type("Terminal: Create New Terminal", delay=80)
        time.sleep(1)

        # Enter ile calistir
        page.keyboard.press("Enter")
        print("[+] Komut gonderildi: Terminal: Create New Terminal")

        # noVNC'den gorebilmek icin bekle
        print("[*] 10 saniye bekleniyor - noVNC'den kontrol edin...")
        time.sleep(10)

        browser.close()
        print("[+] Tamamlandi")


if __name__ == "__main__":
    main()
