"""
voice_generator.py — ElevenLabs & Edge-TTS seslendirme modulu.
ElevenLabs icerik tipine gore optimize parametrelerle, Edge-TTS fallback.
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import Optional

import edge_tts
import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


# ══════════════════════════════════════════════════
# Yardimci — Ses ID secimi
# ══════════════════════════════════════════════════

def get_voice_id(content_type: str = "general") -> str:
    """Dil ayarina gore ElevenLabs ses ID'si dondurur."""
    lang_voices = cfg.ELEVENLABS_VOICES.get(cfg.LANGUAGE, cfg.ELEVENLABS_VOICES["tr"])
    return lang_voices.get("default", lang_voices.get("male"))


def get_voice_settings(voice_style: str) -> dict:
    """
    Icerik tipine gore optimize ElevenLabs ses parametreleri dondurur.
    config.ELEVENLABS_VOICE_SETTINGS'den okur.
    """
    settings_map = getattr(cfg, "ELEVENLABS_VOICE_SETTINGS", {})
    return settings_map.get(voice_style, settings_map.get("default", {
        "stability": 0.45,
        "similarity_boost": 0.75,
        "style": 0.35,
        "speed": 1.05,
    }))


# ══════════════════════════════════════════════════
# ElevenLabs TTS
# ══════════════════════════════════════════════════

def generate_voice_elevenlabs(
    text: str,
    output_path: Path,
    voice_id: Optional[str] = None,
    voice_style: str = "default",
) -> Optional[Path]:
    """
    ElevenLabs TTS API ile premium seslendirme uretir.

    Args:
        text:        Seslendirilecek metin
        output_path: .mp3 kaydedilecek yol
        voice_id:    ElevenLabs voice ID (None = config'den varsayilan)
        voice_style: Ses stili (cheerful/sad/inspirational/dramatic/default)

    Returns:
        Olusturulan .mp3 dosyasinin Path'i, hata halinde None
    """
    if not cfg.ELEVENLABS_API_KEY or len(cfg.ELEVENLABS_API_KEY) < 20:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = _clean_text(text)

    voice_id = voice_id or get_voice_id()
    settings = get_voice_settings(voice_style)

    headers = {
        "xi-api-key": cfg.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text[:4800],
        "model_id": cfg.ELEVENLABS_MODEL,
        "voice_settings": {
            "stability":         settings["stability"],
            "similarity_boost":  settings["similarity_boost"],
            "style":             settings["style"],
            "use_speaker_boost": True,
            "speed":             settings["speed"],
        },
        "output_format": "mp3_44100_128",
    }
    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"

    try:
        logger.info(f"  ElevenLabs TTS ({voice_style}) deneniyor...")
        with httpx.Client(timeout=45) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200 and len(resp.content) > 500:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                size_kb = output_path.stat().st_size / 1024
                logger.info(f"  ElevenLabs ses kaydedildi: {output_path.name} ({size_kb:.1f} KB)")
                return output_path
            else:
                logger.warning(f"ElevenLabs durum: {resp.status_code} — Edge-TTS'e geciliyor")
    except Exception as e:
        logger.warning(f"ElevenLabs hatasi: {e} — Edge-TTS'e geciliyor")

    return None


# ══════════════════════════════════════════════════
# Edge-TTS (Ucretsiz Fallback)
# ══════════════════════════════════════════════════

# Edge-TTS icerik tipine gore hiz ve pitch ayarlari
# Gelistirilmis versiyon: daha dogal ve profesyonel ses profilleri
EDGE_TTS_STYLE = {
    "cheerful":      {"rate": "+15%", "pitch": "+8Hz",  "voice_key": "female", "volume": "+10%"},
    "sad":           {"rate": "-10%", "pitch": "-2Hz",  "voice_key": "female", "volume": "+5%"},
    "inspirational": {"rate": "+8%",  "pitch": "+3Hz",  "voice_key": "male",   "volume": "+8%"},
    "dramatic":      {"rate": "-15%", "pitch": "-4Hz",  "voice_key": "male",   "volume": "+6%"},
    "default":       {"rate": "+2%",  "pitch": "+1Hz",  "voice_key": "default", "volume": "+0%"},
}


def _apply_ssml_pauses(text: str, voice_style: str) -> str:
    """
    Noktalama isareti ve icerik tipine gore SSML duraklamalari ekler.
    Bu sayede Edge-TTS dramatik/komik/duygusal ritim kazanir.
    Gelistirilmis versiyon: daha dogal konuşma ritmi.
    """
    import re
    # Dogal konuşma akisi için minum mola (mesajlari kaldırdik)
    pause_ms = {
        "dramatic":      {".": 200, "?": 150, "!": 180, ",": 80, ";": 100, ":": 120},
        "sad":           {".": 180, "?": 140, "!": 160, ",": 70, ";": 90, ":": 110},
        "inspirational": {".": 150, "?": 120, "!": 180, ",": 60, ";": 80, ":": 100},
        "cheerful":      {".": 100, "?": 80,  "!": 90,  ",": 50, ";": 70,  ":": 60},
        "default":       {".": 120, "?": 100, "!": 110, ",": 60, ";": 80,  ":": 90},
    }.get(voice_style, {".": 120, "?": 100, "!": 110, ",": 60, ";": 80, ":": 90})

    result = ""
    for char in text:
        result += char
        if char in pause_ms:
            ms = pause_ms[char]
            result += f'<break time="{ms}ms"/>'

    # Paragraf sonu için kisa duraklama
    result = re.sub(r'\n\n', '<break time="200ms"/>', result)
    # Satır sonu için cok kisa duraklama
    result = re.sub(r'\n', '<break time="100ms"/>', result)

    return result


def generate_voice_edge(
    text: str,
    output_path: Path,
    voice_name: Optional[str] = None,
    voice_style: str = "default",
) -> Optional[Path]:
    """Microsoft Edge Neural TTS ile ucretsiz, dogal seslendirme uretir.
    Icerik tipine gore hiz, pitch, volume ve SSML duraklamalari otomatik ayarlanir.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean_text = _clean_text(text)

    style_cfg = EDGE_TTS_STYLE.get(voice_style, EDGE_TTS_STYLE["default"])
    rate  = style_cfg["rate"]
    pitch = style_cfg["pitch"]
    volume = style_cfg.get("volume", "+0%")

    if not voice_name:
        lang_voices = getattr(cfg, "EDGE_TTS_VOICES", {}).get(cfg.LANGUAGE, {})
        voice_key   = style_cfg.get("voice_key", "default")
        voice_name  = lang_voices.get(voice_key) or lang_voices.get("default", "tr-TR-EmelNeural")

    logger.info(f"  Edge-TTS ({voice_name}, rate={rate}, pitch={pitch}, volume={volume}, stil={voice_style})...")

    # SSML duraklamalari ekle — daha dogal ritim
    ssml_text = _apply_ssml_pauses(clean_text, voice_style)

    async def _produce_ssml():
        communicate = edge_tts.Communicate(ssml_text, voice_name, rate=rate, pitch=pitch, volume=volume)
        await communicate.save(str(output_path))

    async def _produce_plain():
        # SSML basarisiz olursa sade metin ile dene
        communicate = edge_tts.Communicate(clean_text, voice_name, rate=rate, pitch=pitch, volume=volume)
        await communicate.save(str(output_path))

    for attempt in range(3):
        try:
            producer = _produce_ssml if attempt == 0 else _produce_plain
            asyncio.run(producer())
            if output_path.exists() and output_path.stat().st_size > 500:
                size_kb = output_path.stat().st_size / 1024
                logger.info(f"  Edge-TTS ses kaydedildi: {output_path.name} ({size_kb:.1f} KB)")
                return output_path
        except Exception as e:
            logger.warning(f"Edge-TTS deneme {attempt+1} hatasi: {e}")
            time.sleep(1)

    return None


# ══════════════════════════════════════════════════
# Ana ses uretici — ElevenLabs -> Edge-TTS
# ══════════════════════════════════════════════════

def generate_voice(
    text: str,
    output_path: Path,
    voice_id: Optional[str] = None,
    voice_style: str = "default",
) -> Optional[Path]:
    """
    Seslendirme uretir.
    Oncelik: ElevenLabs (premium, key varsa) -> Edge-TTS (ucretsiz, guvenilir).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. ElevenLabs — premium kalite
    result = generate_voice_elevenlabs(
        text=text,
        output_path=output_path,
        voice_id=voice_id,
        voice_style=voice_style,
    )
    if result:
        return result

    # 2. Edge-TTS — icerik tipine gore optimize edilmis
    return generate_voice_edge(text=text, output_path=output_path, voice_style=voice_style)


# ══════════════════════════════════════════════════
# Sahne bazli ses uretimi
# ══════════════════════════════════════════════════

def generate_scene_voices(
    scenes: list,
    output_dir: Path,
    video_id: str,
    voice_style: str = "default",
) -> list:
    """
    Her sahne icin ayri ses dosyasi uretir.

    Args:
        scenes:      script["scenes"] listesi
        output_dir:  Cikti klasoru
        video_id:    Video kimligi
        voice_style: ElevenLabs ses stili

    Returns:
        Her sahne icin ses dosyasi yollari listesi
    """
    audio_files = []
    for scene in scenes:
        idx   = scene.get("index", len(audio_files) + 1)
        chunk = scene.get("narration_chunk", "")
        if not chunk.strip():
            audio_files.append(None)
            continue

        out  = output_dir / f"{video_id}_scene_{idx:02d}.mp3"
        path = generate_voice(text=chunk, output_path=out, voice_style=voice_style)
        audio_files.append(path)

    return audio_files


def generate_full_narration(
    narration: str,
    output_dir: Path,
    video_id: str,
    content_type: str = "general",
) -> Optional[Path]:
    """
    Tam senaryoyu tek ses dosyasina donusturur.

    Args:
        narration:    Tam seslendirme metni
        output_dir:   Cikti klasoru
        video_id:     Video ID
        content_type: Icerik tipi (ElevenLabs ses stili icin)

    Returns:
        .mp3 dosya yolu
    """
    # Icerik tipinden ses stili bul
    voice_style = "default"
    for sched in getattr(cfg, "CONTENT_SCHEDULE", []):
        if sched.get("type") == content_type:
            voice_style = sched.get("voice_style", "default")
            break

    out = output_dir / f"{video_id}_narration.mp3"
    return generate_voice(
        text=narration,
        output_path=out,
        voice_id=get_voice_id(content_type),
        voice_style=voice_style,
    )


# ══════════════════════════════════════════════════
# Yardimci fonksiyonlar
# ══════════════════════════════════════════════════

def _clean_text(text: str) -> str:
    """TTS icin metni temizler."""
    # Markdown isaretlerini kaldir
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*',     r'\1', text)
    text = re.sub(r'#+\s*',         '',    text)
    text = re.sub(r'\[.*?\]\(.*?\)', '',   text)
    # Fazla boslukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def check_quota() -> dict:
    """ElevenLabs kota bilgisini ceker."""
    if not cfg.ELEVENLABS_API_KEY:
        return {"used": 0, "limit": 0, "remaining": 0, "active": False}
    try:
        headers = {"xi-api-key": cfg.ELEVENLABS_API_KEY}
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{ELEVENLABS_BASE}/user", headers=headers)
            resp.raise_for_status()
            data = resp.json()
        sub       = data.get("subscription", {})
        used      = sub.get("character_count", 0)
        limit     = sub.get("character_limit", 0)
        remaining = limit - used
        logger.info(f"ElevenLabs kota: {used:,}/{limit:,} karakter ({remaining:,} kaldi)")
        return {"used": used, "limit": limit, "remaining": remaining, "active": True}
    except Exception as e:
        logger.warning(f"ElevenLabs kota bilgisi alinamadi: {e}")
        return {"used": 0, "limit": 0, "remaining": 0, "active": False}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    quota = check_quota()
    print(f"ElevenLabs Kota: {quota}")

    test_text = "Merhaba! Bu bir test seslendirmesi. YouTube Shorts otomasyonu calisiyor!"
    out_path  = cfg.TEMP_DIR / "test_voice.mp3"
    result    = generate_voice(text=test_text, output_path=out_path, voice_style="dramatic")
    if result:
        print(f"✓ Basarili: {result}")
    else:
        print("✗ Ses üretilemedi")
