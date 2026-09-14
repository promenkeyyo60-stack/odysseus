"""
script_writer.py — GPT-4o / Gemini ile YouTube Shorts senaryosu yazar.
Her video icin SCENES_PER_VIDEO kadar sahne, sinematik visual prompt'larla.
"""

import json
import logging
from typing import Optional

from openai import OpenAI

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════
# Senaryo Sablonu — Profesyonel, Cok Sahneli
# ══════════════════════════════════════════════════

SCRIPT_TEMPLATE = """
Bir YouTube Shorts senaryosu yaz. Su kurallara kesinlikle uy:

KONU: {topic}
ISLEN ACISI: {angle}
HOOK (Ilk 3 sn): {hook}
ICERIK TIPI: {content_type} — {prompt_hint}
DIL: {language}
HEDEF SURE: {duration} saniye
SAHNE SAYISI: Tam olarak {scenes_count} sahne olmali (daha az KABUL EDILMEZ)

═══ SENARYO KURALLARI ═══
✓ Ilk cumle (hook) izleyiciyi ANINDA yakala — soru, sok veya merak.
✓ Konusma dili, samimi ve dogal olsun. Resmi degil.
✓ Kisa cumleler kullan (max 12 kelime/cumle).
✓ Duygusal tepki uyandır: guldurmeli / dokunsun / sok et / ilham ver.
✓ Son sahne CTA olmali: "Begen", "Yorum yap", "Takip et".
✓ Toplam kelime sayisi: {target_words} kelime (~{duration} sn).
✓ Her sahne icin sinematik, detayli Ingilizce gorsel prompt yaz.
✓ Sahne geçişleri akıcı olsun, her sahne birbirini bağlasın.

═══ GORSEL PROMPT KURALLARI ═══
✓ Her visual_prompt INGILIZCE ve en az 25 kelime olmali.
✓ Sahneye ozgu karakter, mekan, duygu ve hareket ekle.
✓ "cinematic vertical 9:16" ve "photorealistic" her promptta olmali.
✓ Icerik tipine gore stil:
   - dramatik: "dark moody cinematic, dramatic shadows, high contrast"
   - komik: "vibrant colors, playful lighting, dynamic composition"
   - duygusal: "soft warm golden hour lighting, emotional depth, shallow DOF"
   - motivasyon: "epic cinematic, powerful composition, golden light"
✓ Her sahne farklı kompozisyon ve perspektif kullan.

═══ PROFESYONEL SAHNE YAPISI ═══
✓ Sahne 1: Hook + Dramatik açılış (görsel şok)
✓ Sahne 2-3: Hikaye gelişimi + Detaylar
✓ Sahne 4: Tension/climax (en yüksek nokta)
✓ Sahne 5: Resolution + CTA (eylem çağrısı)

═══ CIKTI FORMATI (JSON) ═══
{{
  "title": "YouTube basligi (emoji ile, max 70 karakter, Turkce)",
  "description": "Video aciklamasi (SEO icin, 150-200 kelime, hashtagler dahil)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "narration": "Tam seslendirme metni (tek blok, noktalama isaretleriyle, dogal konusma ritmi)",
  "scenes": [
    {{
      "index": 1,
      "duration_seconds": 8,
      "narration_chunk": "Bu sahnede soylenecek metin (2-3 cumle max)",
      "visual_prompt": "Detailed cinematic English prompt for AI image/video generation, photorealistic, vertical 9:16, dramatic opening shot",
      "mood": "dramatic"
    }},
    {{
      "index": 2,
      "duration_seconds": 10,
      "narration_chunk": "Ikinci sahne metni",
      "visual_prompt": "Another detailed cinematic English prompt, different composition, character action",
      "mood": "tense"
    }}
  ],
  "thumbnail_prompt": "Eye-catching YouTube thumbnail prompt (English, bold, vivid, vertical, high contrast)",
  "total_estimated_seconds": {duration}
}}
"""


def estimate_target_words(duration_sec: int) -> int:
    """
    Turkce/Ingilizce icin ortalama konusma hizi: ~140 kelime/dakika.
    Shorts icin biraz daha hızlı tempo kullanılır (izleyici attention span kisa).
    """
    return int((duration_sec / 60) * 140)


def write_script(topic_data: dict) -> dict:
    """
    GPT-4o / Gemini ile profesyonel, cok sahneli senaryo yazar.

    Args:
        topic_data: topic_finder.py'den gelen topic dict

    Returns:
        Senaryo dict (title, description, narration, scenes, ...)
    """
    from pipeline.llm_client import call_llm_json

    content_config = topic_data.get("content_config", {})
    target_words   = estimate_target_words(cfg.TARGET_DURATION_SECONDS)
    scenes_count   = getattr(cfg, "SCENES_PER_VIDEO", 5)

    lang_instruction = {
        "tr":   "TURKCE yaz — tam anlamiyla Turkce, Turk kulturune uygun.",
        "en":   "Write in ENGLISH — native, casual American/British English.",
        "both": "Icerik tipine gore dil sec: komik=TR, motivasyon=EN olabilir.",
    }.get(cfg.LANGUAGE, "TURKCE yaz.")

    prompt = SCRIPT_TEMPLATE.format(
        topic        = topic_data.get("topic", "Viral konu"),
        angle        = topic_data.get("angle", ""),
        hook         = topic_data.get("hook", ""),
        content_type = content_config.get("type", "genel"),
        prompt_hint  = content_config.get("prompt_hint", ""),
        language     = f"{cfg.LANGUAGE} — {lang_instruction}",
        duration     = cfg.TARGET_DURATION_SECONDS,
        target_words = target_words,
        scenes_count = scenes_count,
    )

    system = f"""Sen profesyonel bir YouTube Shorts icerik yazari ve video yap-mcisisin.
{lang_instruction}
SADECE JSON formatinda cikti ver, aciklama yazma.
Visual prompt'lar her zaman INGILIZCE olmali (AI video uretimi icin).
Narration {cfg.LANGUAGE} dilinde olmali.
Tam olarak {scenes_count} adet sahne uret — daha az kesinlikle kabul edilmez."""

    script = call_llm_json(system, prompt, temperature=0.82, max_tokens=2800)

    if script and "title" in script and "narration" in script and "scenes" in script:
        scenes = script.get("scenes", [])

        # Sahne sayisini dogrula — eksikse fallback sahneler ekle
        if len(scenes) < scenes_count:
            logger.warning(f"LLM {len(scenes)} sahne üretti, {scenes_count} gerekli. Eksikler tamamlanıyor.")
            scenes = _pad_scenes(scenes, scenes_count, script, cfg.TARGET_DURATION_SECONDS)
            script["scenes"] = scenes

        # Sahne indekslerini normalize et ve visual_prompt'u zenginlestir
        style_suffix = getattr(cfg, "VISUAL_STYLE_SUFFIX", "cinematic, photorealistic")
        for i, scene in enumerate(script["scenes"]):
            scene["index"] = i + 1
            if "duration_seconds" not in scene:
                scene["duration_seconds"] = max(
                    cfg.TARGET_DURATION_SECONDS // max(len(scenes), 1), 4
                )
            # Visual prompt'a stil suffix ekle (yoksa)
            vp = scene.get("visual_prompt", f"Cinematic scene {i+1}")
            if "photorealistic" not in vp.lower():
                scene["visual_prompt"] = f"{vp}, {style_suffix}"

        logger.info(
            f"  Senaryo hazir: '{script['title'][:50]}...' "
            f"({len(script['scenes'])} sahne)"
        )
        return script

    # Fallback senaryo
    logger.warning("LLM senaryo donus yapmadi, fallback kullaniliyor")
    return _fallback_script(topic_data)


def _pad_scenes(scenes: list, target: int, script: dict, total_dur: int) -> list:
    """Eksik sahneleri narration'dan bolereck tamamlar."""
    narration = script.get("narration", "")
    sentences = [s.strip() for s in narration.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    style_suffix = getattr(cfg, "VISUAL_STYLE_SUFFIX", "cinematic, photorealistic")

    while len(scenes) < target:
        idx = len(scenes) + 1
        chunk = sentences[idx - 1] if idx - 1 < len(sentences) else f"Sahne {idx}"
        scenes.append({
            "index": idx,
            "duration_seconds": max(total_dur // target, 4),
            "narration_chunk": chunk,
            "visual_prompt": f"Cinematic dramatic scene {idx}, vertical 9:16 composition, {style_suffix}",
            "mood": "dramatic",
        })
    return scenes[:target]


def _fallback_script(topic_data: dict) -> dict:
    """API hatasi durumunda 5 sahne iceren basit bir senaryo dondurcur."""
    topic = topic_data.get("topic", "Viral Konu")
    hook  = topic_data.get("hook", "Bunu bilmek ister misin?")
    style = getattr(cfg, "VISUAL_STYLE_SUFFIX", "cinematic, photorealistic")
    scenes_count = getattr(cfg, "SCENES_PER_VIDEO", 5)

    sentences = [
        hook,
        f"{topic} hakkinda cok az kisi bunu biliyor.",
        "Arastirmacilar yillarca bu konuyu cozemedi.",
        "Gercek ortaya ciktiginda herkes sasirdi.",
        "Bu videoyu begen ve takip etmeyi unutma!",
    ]

    moods = ["dramatic", "tense", "mysterious", "shocking", "energetic"]
    dur_each = max(cfg.TARGET_DURATION_SECONDS // scenes_count, 4)

    scenes = [
        {
            "index": i + 1,
            "duration_seconds": dur_each,
            "narration_chunk": sentences[i] if i < len(sentences) else f"Sahne {i+1}.",
            "visual_prompt": (
                f"Cinematic vertical shot related to '{topic}', scene {i+1}, "
                f"dramatic composition, {style}"
            ),
            "mood": moods[i % len(moods)],
        }
        for i in range(scenes_count)
    ]

    return {
        "title": f"🔴 {topic[:60]}",
        "description": f"{topic} hakkinda her sey bu videoda! #shorts #viral #trending",
        "tags": ["shorts", "viral", "trending", "turkiye", "kesfet"],
        "narration": " ".join(sentences),
        "scenes": scenes,
        "thumbnail_prompt": f"Eye-catching YouTube thumbnail about {topic}, bold text, vivid colors, vertical",
        "total_estimated_seconds": cfg.TARGET_DURATION_SECONDS,
    }


def enrich_script_with_seo(script: dict, topic_data: dict) -> dict:
    """Mevcut senaryoya SEO keyword'lerini ekler."""
    keywords = topic_data.get("keywords", [])
    if keywords and script.get("tags"):
        existing = set(script["tags"])
        for kw in keywords:
            existing.add(kw.lower())
        script["tags"] = list(existing)[:15]

    if keywords and script.get("description"):
        hashtags = " ".join(f"#{k.replace(' ', '')}" for k in keywords[:8])
        if hashtags not in script["description"]:
            script["description"] += f"\n\n{hashtags} #shorts #viral #kesfet"

    return script


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json

    test_topic = {
        "topic": "1587'de 115 kisilik Roanoke kolonisi bir gecede kayboldu",
        "angle": "Tarihin en buyuk gizemlerinden biri — hala cozulemedi",
        "hook": "115 kisi bir anda yok oldu. Geride sadece tek bir kelime kaldi.",
        "keywords": ["gizem", "tarih", "kayip", "koloni", "roanoke", "viral"],
        "content_config": {
            "type": "dramatik",
            "label": "Dramatik",
            "prompt_hint": "Gercek hayattan dramatik, gerilimli veya sasirtici bir olay.",
            "hook_style": "gerilimli ve merak uyandiran acilis",
            "voice_style": "dramatic",
        },
    }

    script = write_script(test_topic)
    script = enrich_script_with_seo(script, test_topic)
    print(json.dumps(script, ensure_ascii=False, indent=2))
