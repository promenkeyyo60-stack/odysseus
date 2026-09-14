"""
video_generator.py — AI gorsel/video uretim modulu.
Oncelik: Runway -> Luma -> DALL-E 3 -> Pollinations (ucretsiz)
Tum sahneler paralel uretilir. Her prompta otomatik estetik stil suffix eklenir.
"""

import logging
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg
from .visual_templates import enhance_scene_visuals

logger = logging.getLogger(__name__)

RUNWAY_BASE = "https://api.dev.runwayml.com/v1"
LUMA_BASE   = "https://api.lumalabs.ai/dream-machine/v1"


# ══════════════════════════════════════════════════
# Prompt Zenginlestirme
# ══════════════════════════════════════════════════

def _enrich_prompt(prompt: str, mood: str = "") -> str:
    """
    Gorsel prompt'una config'den stil suffix ekler.
    Zaten 'photorealistic' iceriyorsa suffix eklemez.
    """
    suffix = getattr(cfg, "VISUAL_STYLE_SUFFIX", "cinematic, photorealistic")
    if "photorealistic" in prompt.lower():
        return prompt

    mood_extras = {
        "dramatic":     "dark moody cinematic, dramatic shadows, high contrast",
        "tense":        "suspenseful atmosphere, deep shadows, cold tones",
        "mysterious":   "fog, mist, mysterious lighting, eerie atmosphere",
        "shocking":     "intense lighting, wide angle, dramatic perspective",
        "energetic":    "vibrant colors, dynamic composition, motion blur",
        "sad":          "soft warm golden hour, emotional depth, shallow DOF",
        "inspirational":"epic wide shot, golden light, powerful composition",
        "cheerful":     "bright vibrant colors, playful lighting, warm tones",
        "calm":         "soft natural light, peaceful composition, pastel tones",
    }
    extra = mood_extras.get(mood.lower(), "")
    enriched = f"{prompt}, {suffix}"
    if extra:
        enriched += f", {extra}"
    return enriched


# ══════════════════════════════════════════════════
# Runway ML — AI Video Klipler
# ══════════════════════════════════════════════════

def generate_video_runway(
    prompt: str,
    output_path: Path,
    duration: int = 5,
    mood: str = "",
) -> Optional[Path]:
    """Runway Gen-3 Turbo ile dikey AI video klibi uretir."""
    if not cfg.RUNWAY_API_KEY or len(cfg.RUNWAY_API_KEY) < 20:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    enriched = _enrich_prompt(prompt, mood)
    headers = {
        "Authorization": f"Bearer {cfg.RUNWAY_API_KEY}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }
    payload = {
        "model":        cfg.RUNWAY_MODEL,
        "promptText":   f"{enriched}. Vertical 9:16 format, cinematic quality.",
        "ratio":        cfg.RUNWAY_RATIO,
        "duration":     min(duration, 10),
    }

    try:
        logger.info(f"  Runway video uretimi baslatiliyor...")
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{RUNWAY_BASE}/image_to_video", headers=headers, json=payload)
            resp.raise_for_status()
            task = resp.json()

        task_id = task.get("id")
        if not task_id:
            return None

        return _poll_runway_task(task_id, output_path, headers)

    except Exception as e:
        logger.warning(f"Runway baslatma hatasi: {e}")
        return None


def _poll_runway_task(
    task_id: str,
    output_path: Path,
    headers: dict,
    max_wait: int = 300,
    poll_interval: int = 5,
) -> Optional[Path]:
    """Runway task'ini polling ile takip eder."""
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(f"{RUNWAY_BASE}/tasks/{task_id}", headers=headers)
                resp.raise_for_status()
                task = resp.json()

            status = task.get("status", "")
            logger.info(f"  Runway: {status} — {elapsed}sn")

            if status == "SUCCEEDED":
                outputs = task.get("output", [])
                if outputs:
                    return _download_file(outputs[0], output_path)
                return None
            elif status == "FAILED":
                logger.error(f"Runway basarisiz: {task.get('failure', '')}")
                return None
        except Exception as e:
            logger.warning(f"Runway polling hatasi: {e}")

    logger.error(f"Runway timeout ({max_wait}sn)")
    return None


# ══════════════════════════════════════════════════
# Luma AI — AI Video Klipler (alternatif)
# ══════════════════════════════════════════════════

def generate_video_luma(
    prompt: str,
    output_path: Path,
    mood: str = "",
) -> Optional[Path]:
    """Luma Dream Machine ile dikey AI video klibi uretir."""
    if not cfg.LUMA_API_KEY or len(cfg.LUMA_API_KEY) < 20:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    enriched = _enrich_prompt(prompt, mood)
    headers = {
        "Authorization": f"Bearer {cfg.LUMA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt":       f"{enriched}. Vertical 9:16 format, cinematic quality.",
        "aspect_ratio": "9:16",
        "loop":         False,
    }

    try:
        logger.info(f"  Luma video uretimi baslatiliyor...")
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{LUMA_BASE}/generations", headers=headers, json=payload)
            resp.raise_for_status()
            generation = resp.json()

        gen_id = generation.get("id")
        if not gen_id:
            return None

        return _poll_luma_generation(gen_id, output_path, headers)

    except Exception as e:
        logger.warning(f"Luma baslatma hatasi: {e}")
        return None


def _poll_luma_generation(
    gen_id: str,
    output_path: Path,
    headers: dict,
    max_wait: int = 240,
    poll_interval: int = 5,
) -> Optional[Path]:
    """Luma generation'i polling ile takip eder."""
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(f"{LUMA_BASE}/generations/{gen_id}", headers=headers)
                resp.raise_for_status()
                gen = resp.json()

            state = gen.get("state", "")
            logger.info(f"  Luma: {state} — {elapsed}sn")

            if state == "completed":
                video_url = gen.get("assets", {}).get("video")
                if video_url:
                    return _download_file(video_url, output_path)
                return None
            elif state == "failed":
                logger.error(f"Luma basarisiz: {gen.get('failure_reason', '')}")
                return None
        except Exception as e:
            logger.warning(f"Luma polling hatasi: {e}")

    logger.error(f"Luma timeout ({max_wait}sn)")
    return None


# ══════════════════════════════════════════════════
# DALL-E 3 — Yuksek Kalite Statik Gorsel
# ══════════════════════════════════════════════════

def generate_image_dalle(
    prompt: str,
    output_path: Path,
    mood: str = "",
) -> Optional[Path]:
    """DALL-E 3 ile yuksek kalite dikey gorsel uretir."""
    if not cfg.OPENAI_API_KEY or len(cfg.OPENAI_API_KEY) < 20:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=cfg.OPENAI_API_KEY)
    except Exception:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched = _enrich_prompt(prompt, mood)

    try:
        logger.info(f"  DALL-E 3 gorsel uretiliyor...")
        resp = client.images.generate(
            model="dall-e-3",
            prompt=f"{enriched}. Vertical portrait orientation, 9:16 aspect ratio.",
            size="1024x1792",
            quality="standard",
            n=1,
        )
        image_url = resp.data[0].url
        if image_url:
            return _download_file(image_url, output_path)
    except Exception as e:
        logger.warning(f"DALL-E 3 hatasi: {e}")

    return None


# ══════════════════════════════════════════════════
# Pollinations.ai — Ucretsiz AI Gorsel
# ══════════════════════════════════════════════════

def generate_image_pollinations(
    prompt: str,
    output_path: Path,
    mood: str = "",
    width: int = 720,
    height: int = 1280,
) -> Optional[Path]:
    """Pollinations.ai ile ucretsiz, yuksek cozunurluklu dikey AI gorseli uretir."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    enriched = _enrich_prompt(prompt, mood)
    encoded  = urllib.parse.quote(enriched)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&enhance=true"

    for attempt in range(3):
        try:
            logger.info(f"  AI gorseli uretiliyor (Pollinations, deneme {attempt+1})...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
                if len(data) > 5000:  # En az 5KB
                    output_path.write_bytes(data)
                    size_kb = output_path.stat().st_size / 1024
                    logger.info(f"  Gorsel kaydedildi: {output_path.name} ({size_kb:.1f} KB)")
                    return output_path
        except Exception as e:
            logger.warning(f"Pollinations hatasi (deneme {attempt+1}): {e}")
            time.sleep(3)

    return None


# ══════════════════════════════════════════════════
# Fallback — Sinematik Kart (Asla hata vermez)
# ══════════════════════════════════════════════════

def generate_fallback_card(
    text: str,
    output_path: Path,
    width: int = 720,
    height: int = 1280,
) -> Path:
    """Tum API'ler basarisiz olursa Pillow ile gradient kart olusturur."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img  = Image.new("RGB", (width, height), color=(12, 14, 22))
    draw = ImageDraw.Draw(img)

    # Koyu gradient arka plan
    for y in range(height):
        ratio = y / height
        r = int(12 + ratio * 30)
        g = int(14 + ratio * 20)
        b = int(22 + ratio * 50)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Altin cerceve
    draw.rectangle([(25, 35), (width - 25, height - 35)], outline=(200, 160, 60), width=2)
    draw.rectangle([(30, 40), (width - 30, height - 40)], outline=(180, 140, 40), width=1)

    img.save(output_path, "JPEG", quality=92)
    logger.info(f"  Fallback kart olusturuldu: {output_path.name}")
    return output_path


# ══════════════════════════════════════════════════
# Tek Sahne Gorsel Uretimi
# ══════════════════════════════════════════════════

def _generate_single_scene(scene: dict, output_dir: Path, video_id: str, prefer_video: bool, content_type: str = "komik") -> dict:
    """Tek bir sahne icin gorsel/video uretir. ThreadPoolExecutor tarafindan cagirilir."""
    idx    = scene.get("index", 1)
    prompt = scene.get("visual_prompt", f"Cinematic scene {idx}")
    mood   = scene.get("mood", "dramatic")
    dur    = min(scene.get("duration_seconds", 5), 10)

    logger.info(f"  Sahne {idx} gorseli uretiliyor ({mood}, {content_type})...")

    # 1. Runway
    if prefer_video and cfg.RUNWAY_API_KEY and len(cfg.RUNWAY_API_KEY) > 20:
        out = output_dir / f"{video_id}_scene_{idx:02d}_runway.mp4"
        result = generate_video_runway(prompt, out, duration=min(dur, 10), mood=mood)
        if result:
            return {"index": idx, "file": result, "type": "video"}

    # 2. Luma
    if prefer_video and cfg.LUMA_API_KEY and len(cfg.LUMA_API_KEY) > 20:
        out = output_dir / f"{video_id}_scene_{idx:02d}_luma.mp4"
        result = generate_video_luma(prompt, out, mood=mood)
        if result:
            return {"index": idx, "file": result, "type": "video"}

    # 3. DALL-E 3
    if cfg.OPENAI_API_KEY and len(cfg.OPENAI_API_KEY) > 20:
        out = output_dir / f"{video_id}_scene_{idx:02d}.png"
        result = generate_image_dalle(prompt, out, mood=mood)
        if result:
            return {"index": idx, "file": result, "type": "image"}

    # 4. Pollinations (ucretsiz)
    out = output_dir / f"{video_id}_scene_{idx:02d}.jpg"
    result = generate_image_pollinations(prompt, out, mood=mood)
    if result:
        return {"index": idx, "file": result, "type": "image"}

    # 5. Fallback kart
    out = output_dir / f"{video_id}_scene_{idx:02d}_card.jpg"
    result = generate_fallback_card(prompt, out)
    return {"index": idx, "file": result, "type": "image"}


# ══════════════════════════════════════════════════
# Ana Orchestrator — Paralel Sahne Uretimi
# ══════════════════════════════════════════════════

def generate_scene_assets(
    scenes: list,
    output_dir: Path,
    video_id: str,
    prefer_video: bool = True,
    content_type: str = "komik",
) -> list:
    """
    Tum sahneler icin gorsel/video PARALEL olarak uretir.
    Oncelik: Runway -> Luma -> DALL-E 3 -> Pollinations -> Sinematik Kart

    Args:
        scenes: Sahne listesi
        output_dir: Cikti dizini
        video_id: Video ID
        prefer_video: Video mi gorsel mi tercih edilsin
        content_type: Icerik tipi (gorsel sablonlari icin)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sahne gorsel prompt'larini icerik tipine gore zenginlestir
    scenes = enhance_scene_visuals(scenes, content_type)

    # Runway/Luma gibi video API'leri sirayla (API rate limit icin)
    # Statik gorsel API'leri paralel
    has_video_api = (
        (cfg.RUNWAY_API_KEY and len(cfg.RUNWAY_API_KEY) > 20) or
        (cfg.LUMA_API_KEY and len(cfg.LUMA_API_KEY) > 20)
    )

    assets = []

    if has_video_api and prefer_video:
        # Video API'leri varsa sirayla cal (rate limit koruma)
        for scene in scenes:
            asset = _generate_single_scene(scene, output_dir, video_id, prefer_video=True, content_type=content_type)
            assets.append(asset)
    else:
        # Sadece gorsel API'leri varsa paralel cal
        max_workers = min(3, len(scenes))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    _generate_single_scene, scene, output_dir, video_id, False, content_type
                ): scene
                for scene in scenes
            }
            for future in as_completed(futures):
                try:
                    asset = future.result()
                    assets.append(asset)
                except Exception as e:
                    scene = futures[future]
                    logger.error(f"Sahne {scene.get('index', '?')} gorsel hatasi: {e}")

        # Indeks sirasina gore sirala
        assets.sort(key=lambda a: a.get("index", 0))

    successful = sum(1 for a in assets if a.get("file"))
    logger.info(f"  {successful}/{len(scenes)} sahne gorseli hazir")
    return assets


# ══════════════════════════════════════════════════
# Yardimci
# ══════════════════════════════════════════════════

def _download_file(url: str, output_path: Path) -> Optional[Path]:
    """URL'den dosya indirir."""
    try:
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)
        size_kb = output_path.stat().st_size / 1024
        logger.info(f"  Indirildi: {output_path.name} ({size_kb:.1f} KB)")
        return output_path
    except Exception as e:
        logger.error(f"Indirme hatasi: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_prompt = "A dramatic close-up of an ancient stone with mysterious glowing symbols, dark underground chamber"
    out = cfg.TEMP_DIR / "test_visual.jpg"
    result = generate_image_pollinations(test_prompt, out, mood="dramatic")
    print(f"Test gorseli: {result}")
