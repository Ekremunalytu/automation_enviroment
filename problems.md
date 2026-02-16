# Proje Analizi - Hata ve Eksikler

## Bulgular (oncelik sirasiyla)

1. Yuksek: Test altyapisinda "DB yoksa skip" akis calismiyor.
   - `tests/conftest.py:75` satirinda `Base.metadata.create_all(bind=engine)` DB baglantisi olmadan once calisiyor.
   - `tests/conftest.py:167` altindaki skip kontrolu bu asamadan sonra geldiginden etkisiz kaliyor.
   - Sonuc: DB bagimsiz testler bile setup asamasinda fail oluyor.

2. Yuksek: `createExtension` akisinda extension secimi belirsiz (yanlis kaydi secme riski).
   - `schemas/schemas.py:455` ve `scanner/service.py:235` sadece `name` kabul ediyor.
   - `scanner/json_parser.py:207` ve `scanner/json_parser.py:216` ilk eslesen dizini donduruyor.
   - Ayni `name` farkli `publisher/version` ile varsa sonuc deterministik degil.

3. Yuksek: Bazi okuma endpointlerinde coklu eslesme kontrolu yok.
   - `crud/crud.py:477`, `crud/crud.py:508`, `crud/crud.py:546`, `crud/crud.py:585`, `crud/crud.py:622` akislari `.first()` kullaniyor.
   - Sadece `name` ile cagrida yanlis extension verisi donebilir.

4. Orta: `get_db` icinde `SessionLocal()` hata verirse `db.close()` ikinci bir hata uretebilir.
   - `core/deps.py:107`, `core/deps.py:118`
   - `db` degiskeni olusmadan `finally` bloguna dusulurse `UnboundLocalError` riski var.

5. Orta: API 500 cevaplarinda ic exception mesaji disariya siziyor.
   - `routers/core.py:225`, `routers/core.py:288`, `routers/core.py:323`, `routers/core.py:402`, `routers/core.py:443`
   - Hata detaylarinin client'a acik verilmesi bilgi sizintisi riski olusturuyor.

6. Orta: `IntegrityError` durumlarinin tamami duplicate gibi map ediliyor.
   - `crud/crud.py:314`, `crud/crud.py:318`
   - Duplicate disi integrity problemleri de "Extension already exists" olarak donebilir.

7. Orta: Pagination parametrelerinde negatif deger validasyonu yok.
   - `routers/core.py:294`
   - `skip=-1` veya `limit=-1` gibi istekler DB seviyesinde hata uretip 500'e dusebilir.

8. Dusuk: `_VSCODE_FIELDS` tanimli ama `parse_extra_fields` icinde kullanilmiyor.
   - `scanner/json_parser.py:737`, `scanner/json_parser.py:804`
   - Bazi VS Code alanlari `extra_fields` icine yanlis siniflanabilir.

9. Dusuk: JSON parse katmaninda genis `except Exception` ve sessiz swallow var.
   - `scanner/json_parser.py:99`
   - Hata gozlemlenebilirligi dusuyor.

## Eksik Parcalar (Roadmap'e Gore)

1. Dynamic analysis tarafinda planlanan kritik moduller henuz yok:
   - `documents/automation_todo.md:141` (extension installer)
   - `documents/automation_todo.md:147` (trigger engine)
   - `documents/automation_todo.md:159` (process/network/fs monitor moduleri)
   - Kodda `executor/extension_manager.py`, `executor/triggers.py`, `executor/monitors/*` bulunmuyor.

2. Analysis sonuclarini saklayacak DB yapilari henuz yok:
   - `documents/automation_todo.md:186`
   - Kodda `analysis_runs`, `analysis_network_events`, `analysis_process_events`, `analysis_fs_events` tablolari yok.

3. Analyze API endpointleri henuz yok:
   - `documents/automation_todo.md:211`
   - `routers/` altinda `/analyze/...` endpointi bulunmuyor.

4. Dokumanda acik gorunen bug maddeleri henuz acik:
   - `documents/automation_todo.md:121`

## Calistirilan Kontroller

1. `ruff check .` -> basarili.
2. `pytest -q tests/executor` -> 3/3 basarili.
3. `pytest -q` -> DB erisimi olmadigi icin setup asamasinda hata verdi.
4. `pytest -q tests/scanner/test_json_parser.py::TestParseNpmFields::test_parse_standard_npm_fields` -> ayni sebeple setup asamasinda hata verdi.
