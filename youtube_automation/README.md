# YouTube Shorts Otomasyon

Odysseus'un API'lerini kullanarak günde 5 Shorts videosu otomatik üretir.

## Hızlı Başlangıç

```powershell
# youtube_automation/ klasörüne git
cd C:\Users\Ahmet\Desktop\odysseus

# Bağımlılıkları kur (ilk seferinde)
venv\Scripts\python.exe -m pip install -r youtube_automation/requirements.txt

# Test et (1 video üret)
venv\Scripts\python.exe youtube_automation/run.py --test

# Bugünkü 5 videoyu üret
venv\Scripts\python.exe youtube_automation/run.py

# VEYA: BAŞLAT.bat dosyasına çift tıkla
```

## Çalıştırma Modları

| Komut | Açıklama |
|---|---|
| `python run.py --test` | Tek video üret, pipeline'ı test et |
| `python run.py` | Bugünkü 5 videoyu üret (1.5sa arayla) |
| `python run.py --once` | Aynısı, batch sonunda kapanır |
| `python run.py --continuous` | Sürekli çalış, her gün üretir |
| `python run.py --type komik` | Sadece komik tipte 1 video |

## Pipeline Akışı

```
NewsAPI trending haberler
        ↓
GPT-4o konu seçimi + hook
        ↓
GPT-4o senaryo + sahne açıklamaları
        ↓
ElevenLabs seslendirme (.mp3)
        ↓
Runway ML / Luma / DALL-E 3 görsel üretimi
        ↓
JSON2Video montaj + altyazı + render
        ↓
output/YYYY-MM-DD/video.mp4 ✅
```

## İçerik Tipleri (Günlük)

1. **Komik #1** — Komik/absürd günlük hayat
2. **Duygusal** — Dokunan gerçek hikayeler  
3. **Komik #2** — Viral trend/fail
4. **Motivasyon** — İlham verici hikaye/alıntı
5. **Dramatik** — Şaşırtıcı gerçek olaylar

## Ayarlar

`config.py` dosyasından her şeyi değiştirebilirsin:

- `LANGUAGE` — `"tr"` veya `"en"`
- `DAILY_VIDEO_COUNT` — Günlük video sayısı
- `INTERVAL_MINUTES` — Videolar arası bekleme (dakika)
- `TARGET_DURATION_SECONDS` — Video süresi hedefi
- `CONTENT_SCHEDULE` — İçerik tipleri ve sıraları

## YouTube Yükleme (Şimdilik Kapalı)

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials)'dan OAuth2 credentials.json indir
2. `youtube_automation/credentials.json` olarak kaydet
3. `pip install google-api-python-client google-auth-oauthlib`
4. `config.py`'de `YOUTUBE_UPLOAD_ENABLED = True` yap

## Çıktı Yapısı

```
output/
└── 2025-01-15/
    ├── 2025-01-15_01_komik.mp4        ← Final video
    ├── 2025-01-15_01_komik.json       ← Metadata (başlık, açıklama, tags)
    ├── 2025-01-15_02_duygusal.mp4
    ├── 2025-01-15_02_duygusal.json
    └── ...
logs/
└── automation_20250115.log
```

## Sorun Giderme

**API hatası:** `logs/` klasöründeki log dosyasına bak

**ElevenLabs kota:** `python -c "from pipeline.voice_generator import check_quota; check_quota()"`

**Test modu:** `python run.py --test` ile tek adım test et
