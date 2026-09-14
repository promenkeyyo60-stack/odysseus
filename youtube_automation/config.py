"""
config.py — YouTube Shorts Otomasyon Ayarlari
Buradan tum sistemi ozellestirilebilirsin.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasini Odysseus kok dizininden yukle
_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env")

# ══════════════════════════════════════════════════
# API Anahtarlari (otomatik .env'den okunur)
# ══════════════════════════════════════════════════
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
RUNWAY_API_KEY      = os.getenv("RUNWAY_API_KEY", "")
LUMA_API_KEY        = os.getenv("LUMA_API_KEY", "")
JSON2VIDEO_API_KEY  = os.getenv("JSON2VIDEO_API_KEY", "")
NEWS_API_KEY        = os.getenv("NEWS_API_KEY", "")
YOUTUBE_API_KEY     = os.getenv("YOUTUBE_API_KEY", "")

# ══════════════════════════════════════════════════
# Genel Ayarlar
# ══════════════════════════════════════════════════

# Dil: "tr" = Turkce, "en" = Ingilizce, "both" = karisik
LANGUAGE = "tr"

# Kanal temasi (senaryo yaziminda kullanilir)
CHANNEL_THEME = "viral genel eglence — komik, duygusal, motivasyon ve dramatik icerikler"

# Gunluk uretilecek video sayisi (7 adet - 7/7 tam otomasyon için)
DAILY_VIDEO_COUNT = 7

# Videolar arasi bekleme suresi (dakika) - 7/7 mod için optimize
INTERVAL_MINUTES = 60  # 1 saat (7 video için gün içinde bitmesi için)

# Video suresi hedefi (saniye) — Shorts icin 50-60 sn ideal
TARGET_DURATION_SECONDS = 58

# Her video icin minimum sahne sayisi (profesyonel kalite icin)
SCENES_PER_VIDEO = 5

# ══════════════════════════════════════════════════
# Icerik Tipleri (sirali dongu) - 7/7 Tam Otomasyon İçin Optimize
# ══════════════════════════════════════════════════
CONTENT_SCHEDULE = [
    {
        "type": "komik",
        "label": "Komik #1",
        "prompt_hint": "Gunluk hayattan komik, absurd veya beklenmedik bir durum. Izleyiciyi guldurmeli.",
        "hook_style": "sok edici veya absurd bir acilis",
        "voice_style": "cheerful",
    },
    {
        "type": "kedi",
        "label": "Kedi #1",
        "prompt_hint": "Kedilerle ilgili komik, sevimli veya viral bir durum. Kedi severleri hedefle.",
        "hook_style": "sevimli ve merak uyandiran acilis",
        "voice_style": "cheerful",
    },
    {
        "type": "tarih",
        "label": "Tarih #1",
        "prompt_hint": "Tarihsel bir olay, gizem veya ilginç gerçek. 'Bunu biliyor muydun?' formatı.",
        "hook_style": "sasirtici tarihsel bilgi ile acilis",
        "voice_style": "dramatic",
    },
    {
        "type": "viral",
        "label": "Viral #1",
        "prompt_hint": "Sosyal medyada trend olan bir konu, challenge veya viral durum. Trend yakala.",
        "hook_style": "trend ile ilgili guncel acilis",
        "voice_style": "cheerful",
    },
    {
        "type": "futbol",
        "label": "Futbol #1",
        "prompt_hint": "Futbol ile ilgili ilginç istatistik, transfer haberi veya tarihsel an.",
        "hook_style": "futbolseverleri yakalayan acilis",
        "voice_style": "inspirational",
    },
    {
        "type": "duygusal",
        "label": "Duygusal",
        "prompt_hint": "Gercek hayat hikayesi ya da haberden esinlenen, dokunan ve dusunduren icerik.",
        "hook_style": "merak uyandiran veya empati kuran bir acilis",
        "voice_style": "sad",
    },
    {
        "type": "motivasyon",
        "label": "Motivasyon",
        "prompt_hint": "Basari, azim veya kisisel gelisim hikayesi ya da guclu alinti. Izleyiciyi harekete gecirmeli.",
        "hook_style": "guclu ve ilham verici acilis cumlesi",
        "voice_style": "inspirational",
    },
]

# ══════════════════════════════════════════════════
# ElevenLabs Ses Ayarlari — Premium Kalite
# ══════════════════════════════════════════════════
# Turkce icin onerilen sesler (ElevenLabs kutuphanesinden):
# Degistirmek icin: https://elevenlabs.io/app/voice-library
ELEVENLABS_VOICES = {
    "tr": {
        "male":    "pNInz6obpgDQGcFmaJgB",   # Adam — Turkceyi iyi destekler
        "female":  "EXAVITQu4vr4xnSDxMaL",   # Bella
        "default": "pNInz6obpgDQGcFmaJgB",
    },
    "en": {
        "male":    "TxGEqnHWrfWFTfGW9XjX",   # Josh
        "female":  "21m00Tcm4TlvDq8ikWAM",   # Rachel
        "default": "TxGEqnHWrfWFTfGW9XjX",
    },
}

# ElevenLabs model: eleven_multilingual_v2 Turkce destekli
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Icerik tipine gore ses parametreleri (ElevenLabs fine-tuning)
ELEVENLABS_VOICE_SETTINGS = {
    "cheerful":    {"stability": 0.35, "similarity_boost": 0.80, "style": 0.55, "speed": 1.10},
    "sad":         {"stability": 0.55, "similarity_boost": 0.75, "style": 0.30, "speed": 0.92},
    "inspirational":{"stability": 0.40, "similarity_boost": 0.82, "style": 0.50, "speed": 1.05},
    "dramatic":    {"stability": 0.30, "similarity_boost": 0.85, "style": 0.65, "speed": 0.95},
    "default":     {"stability": 0.45, "similarity_boost": 0.75, "style": 0.35, "speed": 1.05},
}

# Edge-TTS (ucretsiz, dogal Turkce sesler — ElevenLabs yoksa)
EDGE_TTS_VOICES = {
    "tr": {
        "male":    "tr-TR-AhmetNeural",
        "female":  "tr-TR-EmelNeural",
        "default": "tr-TR-AhmetNeural",
    },
    "en": {
        "male":    "en-US-ChristopherNeural",
        "female":  "en-US-JennyNeural",
        "default": "en-US-ChristopherNeural",
    },
}

# ══════════════════════════════════════════════════
# AI / LLM Ayarlari
# ══════════════════════════════════════════════════
GEMINI_MODEL      = "gemini-3.6-flash"          # En guncel model (2025)
GEMINI_BASE_URL   = "https://generativelanguage.googleapis.com/v1beta/openai"
OPENAI_MODEL      = "gpt-4o"                    # Senaryo yazimi icin
OPENAI_MINI_MODEL = "gpt-4o-mini"              # Hizli gorevler icin (konu secimi vs.)
PRIMARY_LLM       = "gemini" if GEMINI_API_KEY else "openai"

# ══════════════════════════════════════════════════
# Gorsel / Video Uretim Ayarlari
# ══════════════════════════════════════════════════
# Sahne gorseli icin otomatik eklenen estetik stil
VISUAL_STYLE_SUFFIX = (
    "cinematic vertical 9:16 composition, dramatic lighting, "
    "photorealistic, ultra detailed, 4K quality, "
    "retro analog-digital fusion mood, warm ambers, soft greys"
)

# Video montaj tercihi: "moviepy" (profesyonel), "ffmpeg" (temel), "auto" (otomatik secim)
VIDEO_ASSEMBLER_ENGINE = "auto"  # "moviepy", "ffmpeg", veya "auto"

# Ken Burns efekti: zoom + pan animasyonu (FFmpeg fallback icin)
KEN_BURNS_ENABLED = True
KEN_BURNS_ZOOM_FACTOR = 1.08   # %8 zoom-in (cok agresif olmasin)

# ══════════════════════════════════════════════════
# Haber / Konu Kaynaklari
# ══════════════════════════════════════════════════
NEWS_COUNTRY      = "tr"
NEWS_LANGUAGE     = "tr"
NEWS_CATEGORIES   = ["general", "entertainment", "technology", "science"]
NEWS_MAX_ARTICLES = 20

# ══════════════════════════════════════════════════
# JSON2Video Ayarlari
# ══════════════════════════════════════════════════
JSON2VIDEO_BASE_URL = "https://api.json2video.com/v2"
VIDEO_WIDTH         = 720    # Shorts: 9:16
VIDEO_HEIGHT        = 1280
VIDEO_FPS           = 30
USE_LOCAL_FFMPEG    = True   # True: sistemdeki FFmpeg ile yerel render

# Altyazi stili (FFmpeg force_style)
SUBTITLE_FONT_SIZE   = 24
SUBTITLE_FONT_NAME   = "Arial"
SUBTITLE_BOLD        = True
SUBTITLE_OUTLINE     = 2.5
SUBTITLE_MARGIN_V    = 130   # Altta biraz bosluk

# ══════════════════════════════════════════════════
# Runway ML Ayarlari
# ══════════════════════════════════════════════════
RUNWAY_MODEL    = "gen3a_turbo"
RUNWAY_RATIO    = "720:1280"   # Dikey Shorts formati
RUNWAY_DURATION = 5            # Saniye (5 veya 10)

# ══════════════════════════════════════════════════
# Dosya Yollari
# ══════════════════════════════════════════════════
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR   = BASE_DIR / "logs"
TEMP_DIR   = BASE_DIR / "temp"

for _dir in [OUTPUT_DIR, LOGS_DIR, TEMP_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════
# YouTube Yukleme
# ══════════════════════════════════════════════════
YOUTUBE_UPLOAD_ENABLED = True
YOUTUBE_CHANNEL_ID     = "@zihinmolas1"  # Kanalınız: https://www.youtube.com/@zihinmolas1
YOUTUBE_PRIVACY        = "public"
YOUTUBE_CATEGORY_ID    = "24"   # Entertainment

# ══════════════════════════════════════════════════
# Hata Yonetimi
# ══════════════════════════════════════════════════
MAX_RETRIES     = 3
RETRY_DELAY_SEC = 10

# ══════════════════════════════════════════════════
# Test Modu
# ══════════════════════════════════════════════════
TEST_MODE = False
