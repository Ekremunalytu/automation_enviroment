"""Test amaçlı örnek kayıt ekleme scripti."""
import sys
import os

# Proje root'unu path'e ekle
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from database.session import SessionLocal
from models.models import Extension

def seed_test_data():
    db = SessionLocal()
    try:
        # Tüm alanları içeren örnek VS Code extension verisi
        test_extension = Extension(
            # Zorunlu alanlar
            name="python",
            publisher="ms-python",
            engines={"vscode": "^1.95.0"},
            
            # Opsiyonel alanlar - hepsi dolu
            license="MIT",
            displayName="Python",
            description="IntelliSense, linting, debugging, code navigation, code formatting, refactoring, and more for Python.",
            categories=["Programming Languages", "Linters", "Debuggers", "Formatters"],
            keywords=["python", "django", "flask", "pylint", "autopep8"],
            galleryBanner={
                "color": "#1e415e",
                "theme": "dark"
            },
            preview=False,
            badges=[
                {
                    "url": "https://img.shields.io/badge/build-passing-brightgreen",
                    "href": "https://github.com/microsoft/vscode-python",
                    "description": "Build Status"
                }
            ],
            markdown="github",
            qna="marketplace",  # String, bool veya dict olabilir
            sponsor={
                "url": "https://github.com/sponsors/microsoft"
            },
            icon="https://ms-python.gallerycdn.vsassets.io/extensions/ms-python/python/icon.png",
            pricing="Free",
            main="./dist/extension.js",
            web="./dist/web-extension.js",
        )
        
        db.add(test_extension)
        db.commit()
        db.refresh(test_extension)
        
        print(f"✅ Test kaydı eklendi! ID: {test_extension.id}")
        print(f"   Name: {test_extension.name}")
        print(f"   Publisher: {test_extension.publisher}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Hata: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_data()
