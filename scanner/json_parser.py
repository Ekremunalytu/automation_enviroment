import json
from pathlib import Path
from core.config import settings


def parse_json_file(json_path: Path):
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"JSON Okuma hatası ({json_path}): {e}")
        return None


def get_package_json(extension_dir: Path):
    # Doğrudan klasör içinde package.json var mı diye bakıyoruz
    package_path = extension_dir / "package.json"
    if package_path.exists() and package_path.is_file():
        return parse_json_file(package_path)
    return None


def search_extension(extension_name_field: str):
    extension_path = Path(settings.EXTENSION_DIR)  # Path objesine çeviriyoruz

    # Sadece klasörleri al
    all_extensions = [p for p in extension_path.iterdir() if p.is_dir()]

    for extension_dir in all_extensions:
        # Önce package.json'ı çek
        package_data = get_package_json(extension_dir)

        # package.json varsa ve name alanı eşleşiyorsa döndür
        if package_data and package_data.get("name") == extension_name_field:
            return package_data

    return None