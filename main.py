from database.session import engine, SessionLocal
from models.models import Base, Extension
from crud.crud import get_extension_by_id


def init_db() -> None:
    """Veritabanı tablolarını oluşturur."""
    Base.metadata.create_all(bind=engine)
    print("✅ Veritabanı tabloları oluşturuldu.")


def get_db():
    """Veritabanı session dependency'si."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def show_extension(extension_id: int) -> None:
    """Extension bilgisini veritabanından getirir ve gösterir."""
    db = SessionLocal()
    try:
        extension = get_extension_by_id(db, extension_id)
        if extension:
            print(f"\n📦 Extension Bilgisi (ID: {extension.id})")
            print(f"   Name: {extension.name}")
            print(f"   Publisher: {extension.publisher}")
            print(f"   Display Name: {extension.displayName}")
            print(f"   Description: {extension.description}")
            print(f"   Categories: {extension.categories}")
            print(f"   License: {extension.license}")
            print(f"   Engines: {extension.engines}")
        else:
            print(f"❌ ID {extension_id} ile extension bulunamadı.")
    finally:
        db.close()


def main() -> None:
    """Ana giriş noktası."""
    print("🚀 Automation Environment başlatılıyor...")
    
    # Veritabanını başlat
    init_db()
    
    # Test: ID=1 olan extension'ı getir
    show_extension(1)
    
    # TODO: Scanner, Executor, Reporter modüllerini buraya ekle
    print("\n✅ Sistem hazır.")


if __name__ == "__main__":
    main()
