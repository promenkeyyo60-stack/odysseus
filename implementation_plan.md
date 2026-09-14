# 🚀 Odysseus — Profesyonel Seviye Yükseltme Planı

## Mevcut Durum Analizi

Log'u inceledim. Şu an sistem çalışıyor ama **3 kritik zayıflık** var:

| Adım | Şu An | Sorun |
|---|---|---|
| **Senaryo (LLM)** | Gemini Free Tier | Kota dolunca **fallback** — tek sahne, jenerik içerik |
| **Görsel** | Pollinations.ai (ücretsiz) | 43–49 KB, bulanık, hareketsiz jpeg |
| **Ses** | Edge-TTS (ücretsiz) | ElevenLabs 401 veriyor — sahte key |
| **Montaj** | FFmpeg lokal | Teknik olarak iyi, iyileştirme yapılabilir |

> [!CAUTION]
> **Kritik:** ElevenLabs `401 Unauthorized` hatası veriyor. Mevcut key geçersiz.
> Görsel başına sadece 1 sahne üretiliyor (fallback senaryo) — bu yüzden videolar kısa ve basit görünüyor.

---

## Gereken Premium API'ler

### 🔴 ZORUNLU (Kaliteyi doğrudan belirliyor)

| API | Amaç | Plan | Aylık Fiyat |
|---|---|---|---|
| **ElevenLabs** | Türkçe seslendirme | **Starter** ($5) | ~$5 |
| **Google Gemini** | Senaryo yazımı | **Pay-as-you-go** | ~$5–10 |

> [!IMPORTANT]
> Bu ikisi olmadan sistem ya ücretsiz fallback kullanıyor ya da robot sesi üretiyor. **En yüksek etkiyi bunlar sağlar.**

### 🟡 ÖNERİLEN (Görsel kalitesi için)

| API | Amaç | Plan | Aylık Fiyat |
|---|---|---|---|
| **Runway Gen-3 Turbo** | AI video klipler (5sn) | **Standard** ($15) | ~$15 |
| **Luma AI Dream Machine** | AI video klipler (alternatif) | **Standard** ($29.99) | ~$30 |

> [!NOTE]
> Runway veya Luma olmadan görsel = **hareketsiz jpeg**. Sahne başına video klip üretmek sistemi gerçek anlamda profesyonelleştiriyor.

### 🟢 OPSİYONEL

| API | Amaç | Plan | Fiyat |
|---|---|---|---|
| **NewsAPI** | Güncel haber konuları | Developer ($449/ay) veya ücretsiz | Ücretsiz yeterli |
| **OpenAI GPT-4o** | LLM yedek | Pay-as-you-go | ~$5 |

---

## Yapılacak Kod Değişiklikleri

### 1. `config.py` — API key doğrulama + yeni sahne sayısı
- Fake/geçersiz key kontrolü kaldırılacak
- `SCENES_PER_VIDEO = 5` → her video için 5 ayrı sahne
- Senaryo prompt'unu daha detaylı sahne oluşturmaya zorlayacak

### 2. `pipeline/script_writer.py` — Çok sahne + sinematik prompt
- Her video için **5 sahne** üretmeye zorla
- `visual_prompt` alanını Runway/Luma için optimize et
- Roanoke tarzı senaryoda kullandığın kaliteli format'ı şablona yaz

### 3. `pipeline/video_generator.py` — Paralel görsel üretimi
- Tüm sahneleri **paralel** işle (şu an sıralı)
- Runway başarısız → Luma → DALL-E 3 → Pollinations (zincir mevcut ama iyileştirilecek)
- Görsel prompt'lara otomatik stil suffix ekle

### 4. `pipeline/video_assembler.py` — Ken Burns efekti
- Hareketsiz görsellere **zoom/pan animasyonu** ekle (FFmpeg ile ücretsiz)
- Altyazı stilini güncelle: daha büyük font, sarı highlight

### 5. `pipeline/voice_generator.py` — ElevenLabs parametreleri
- Türkçe için optimize ses parametreleri
- Konuşma hızı ve ton içerik tipine göre değişsin

---

## Beklenen Kalite Artışı

| Metrik | Şu An | Sonra |
|---|---|---|
| Sahne sayısı | 1 (fallback) | 5 |
| Görsel kalite | 43 KB jpeg | Runway video / DALL-E 3 |
| Ses kalitesi | Microsoft Edge robot sesi | ElevenLabs doğal Türkçe |
| Video boyutu | ~0.5 MB | ~10–30 MB |
| Üretim süresi | ~15 saniye | ~3–5 dakika |

---

## Open Questions

> [!IMPORTANT]
> **Senden önce ihtiyacım olan bilgiler:**
>
> 1. **Hangi API'leri satın almayı planlıyorsun?** (ElevenLabs + Gemini zorunlu, Runway opsiyonel)
> 2. **API key'lerini `.env` dosyasına kendin ekleyecek misin?** yoksa format nasıl göstereyim?
> 3. Runway/Luma almayacaksan görsel için **DALL-E 3** (OpenAI key gerekli) yeterli mi?

---

## Uygulama Sırası (Onay sonrası)

1. `config.py` → fake key guard'ları kaldır, yeni parametreler
2. `script_writer.py` → 5 sahne zorunlu, kaliteli prompt şablonu
3. `video_assembler.py` → Ken Burns zoom efekti (ücretsiz, anında etki)
4. `voice_generator.py` → ElevenLabs parametreleri
5. `video_generator.py` → paralel üretim + prompt iyileştirme
