"""
run.py - YouTube Shorts Otomasyon Ana Dosyasi

Kullanim:
  python run.py              # Gunluk batch baslat (5 video, 1.5 saat arayla)
  python run.py --test       # Tek video uret (pipeline testi)
  python run.py --once       # Sadece bugunku batchi calistir, kapan
  python run.py --continuous # Surekli calis (her gun otomatik)

Gereksinimler:
  pip install -r youtube_automation/requirements.txt
"""

import argparse
import json
import logging
import sys
import shutil
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# Proje kok dizinini sys.path'e ekle
# ─────────────────────────────────────────────
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

import config as cfg
from scheduler import VideoScheduler

# Pipeline modulleri
from pipeline.topic_finder   import find_daily_topics, select_viral_topic, fetch_all_news
from pipeline.script_writer  import write_script, enrich_script_with_seo
from pipeline.voice_generator import generate_full_narration
from pipeline.video_generator import generate_scene_assets
from pipeline.video_assembler import assemble_video
from pipeline.uploader       import upload_to_youtube


# ─────────────────────────────────────────────
# Logging Kurulumu
# ─────────────────────────────────────────────
def setup_logging() -> None:
    log_file = cfg.LOGS_DIR / f"automation_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    # Gurultulu kutuphaneleri sustur
    for noisy in ["httpx", "httpcore", "openai._base_client", "PIL"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Windows CMD icin stdout encoding'i UTF-8'e zorla
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

logger = logging.getLogger("odysseus.youtube")


# ─────────────────────────────────────────────
# API ve Motor On Kontrol
# ─────────────────────────────────────────────
def check_api_keys() -> bool:
    """Sistem, API ve motor durumlarini kontrol eder."""
    logger.info("[*] Sistem ve Motor Durumu:")

    # LLM
    if cfg.GEMINI_API_KEY:
        logger.info(f"   [OK] AI Metin Motoru: Google Gemini ({cfg.GEMINI_MODEL})")
    elif cfg.OPENAI_API_KEY:
        logger.info(f"   [OK] AI Metin Motoru: OpenAI ({cfg.OPENAI_MODEL})")
    else:
        logger.info("   [BILGI] AI Metin Motoru: Sablon/Fallback modu")

    # Ses
    logger.info("   [OK] Seslendirme Motoru: Microsoft Edge Neural TTS (Dogal Turkce)")
    if cfg.ELEVENLABS_API_KEY and len(cfg.ELEVENLABS_API_KEY) > 20:
        logger.info("   [OK] Seslendirme Yedegi: ElevenLabs")

    # Gorsel
    logger.info("   [OK] Gorsel Uretici: Pollinations AI (Flux/SDXL 720x1280)")
    if cfg.RUNWAY_API_KEY or cfg.LUMA_API_KEY:
        logger.info("   [OK] Video Klip Motoru: Runway / Luma")

    # Montaj
    logger.info("   [OK] Video Montaj: Yerel FFmpeg (9:16 Dikey, Senkron Ses, Altyazi)")

    # Haber
    if cfg.NEWS_API_KEY:
        logger.info("   [OK] Haber Servisi: NewsAPI (Aktif)")
    else:
        logger.info("   [BILGI] Haber Servisi: Trend temalar")

    return True


# ─────────────────────────────────────────────
# Tek Video Pipeline
# ─────────────────────────────────────────────
def produce_video(
    content_config: dict,
    index: int = 1,
    total: int = 1,
    topic_data: dict | None = None,
) -> Path | None:
    """
    Bir Shorts videosu icin tam pipeline calistirir.

    Args:
        content_config: CONTENT_SCHEDULE'deki config (type, label, ...)
        index:          Bugunku video sirasi
        total:          Toplam video sayisi
        topic_data:     Onceden secilmis konu (None = yeni sec)

    Returns:
        Final .mp4 dosyasi yolu veya None
    """
    label = content_config.get("label", f"Video {index}")
    today = datetime.now().strftime("%Y-%m-%d")
    video_id = f"{today}_{index:02d}_{content_config['type']}"

    # Cikti klasoru: output/2025-01-15/
    out_dir  = cfg.OUTPUT_DIR / today
    temp_dir = cfg.TEMP_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    final_path = out_dir / f"{video_id}.mp4"
    meta_path  = out_dir / f"{video_id}.json"  # Metadata kaydi

    logger.info(f"\n>>> [{index}/{total}] {label} - Pipeline Basliyor")
    logger.info(f"   ID: {video_id}")

    try:
        # -- ADIM 1: KONU SEC -----------------------------------------
        logger.info(f"\n[1/5] Konu Secimi (NewsAPI + AI)")
        if not topic_data:
            news = fetch_all_news()
            topic_data = select_viral_topic(content_config, news)
            topic_data["content_config"] = content_config
            topic_data["label"] = label

        logger.info(f"   Konu: {topic_data.get('topic', '?')}")
        logger.info(f"   Hook: {topic_data.get('hook', '?')[:60]}...")

        # -- ADIM 2: SENARYO YAZ --------------------------------------
        logger.info(f"\n[2/5] Senaryo Yazimi (AI)")
        script = write_script(topic_data)
        script = enrich_script_with_seo(script, topic_data)

        scenes = script.get("scenes", [])
        logger.info(f"   Baslik: {script.get('title', '?')[:60]}")
        logger.info(f"   Sahne sayisi: {len(scenes)}")

        # Metadata kaydet (hata olsa bile konu/senaryo korunsun)
        _save_metadata(meta_path, topic_data, script, video_id)

        # -- ADIM 3: SESLENDIR ----------------------------------------
        logger.info(f"\n[3/5] Seslendirme (Neural TTS)")
        narration = script.get("narration", "")
        audio_path = generate_full_narration(
            narration=narration,
            output_dir=temp_dir,
            video_id=video_id,
            content_type=content_config.get("type", "general"),
        )

        if not audio_path:
            logger.warning("   [!] Ses uretilemedi - sessiz video uretilecek")

        # -- ADIM 4: GORSEL URET --------------------------------------
        logger.info(f"\n[4/5] Gorsel/Video Uretimi (AI Gorseller + Konu Bazlı Şablonlar)")
        prefer_video = bool(cfg.RUNWAY_API_KEY or cfg.LUMA_API_KEY)
        content_type = content_config.get("type", "komik")
        scene_assets = generate_scene_assets(
            scenes=scenes,
            output_dir=temp_dir,
            video_id=video_id,
            prefer_video=prefer_video,
            content_type=content_type,
        )

        if not any(a.get("file") for a in scene_assets):
            logger.error("   [X] Hic gorsel uretilemedi!")
            return None

        # -- ADIM 5: MONTAJ + ALTYAZI ---------------------------------
        logger.info(f"\n[5/5] Video Montaji (FFmpeg 9:16 Shorts + Gelişmiş Altyazılar)")
        content_type = content_config.get("type", "komik")
        result = assemble_video(
            script=script,
            scene_assets=scene_assets,
            audio_path=audio_path,
            output_path=final_path,
            content_type=content_type,
        )

        if not result:
            logger.error("   [X] Montaj basarisiz!")
            return None

        # -- OPSIYONEL: YOUTUBE YUKLE ---------------------------------
        if cfg.YOUTUBE_UPLOAD_ENABLED:
            logger.info(f"\n[+] YouTube'a yukleniyor...")
            video_yt_id = upload_to_youtube(
                video_path=final_path,
                title=script.get("title", label),
                description=script.get("description", ""),
                tags=script.get("tags", []),
                content_type=content_config.get("type", "genel"),
            )
            if video_yt_id:
                _update_metadata(meta_path, {"youtube_id": video_yt_id})

        # -- TEMIZLIK -------------------------------------------------
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        size_mb = final_path.stat().st_size / (1024 * 1024)
        logger.info(f"\n[TAMAMLANDI] [{index}/{total}] {label}")
        logger.info(f"   Dosya : {final_path}")
        logger.info(f"   Boyut : {size_mb:.1f} MB")
        logger.info(f"   Baslik: {script.get('title', '')[:55]}")

        return final_path

    except KeyboardInterrupt:
        logger.info("\n[DURDURULDU] Kullanici tarafindan durduruldu")
        raise
    except Exception as e:
        logger.exception(f"Pipeline hatasi [{label}]: {e}")
        return None


# ─────────────────────────────────────────────
# Metadata Yardimcilari
# ─────────────────────────────────────────────
def _save_metadata(path: Path, topic: dict, script: dict, video_id: str) -> None:
    """Video metadata'sini JSON olarak kaydeder."""
    safe_topic = {k: v for k, v in topic.items() if k != "content_config"}
    safe_script = {k: v for k, v in script.items() if k != "scenes"}
    data = {
        "video_id":  video_id,
        "created_at": datetime.now().isoformat(),
        "topic":     safe_topic,
        "title":     script.get("title", ""),
        "description": script.get("description", ""),
        "tags":      script.get("tags", []),
        "thumbnail_prompt": script.get("thumbnail_prompt", ""),
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Metadata kaydedilemedi: {e}")


def _update_metadata(path: Path, updates: dict) -> None:
    """Mevcut metadata'ya guncelleme ekler."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.update(updates)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Metadata guncellenemedi: {e}")


# ─────────────────────────────────────────────
# Ana Giris Noktasi
# ─────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Otomasyon - Gunluk video uretici",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ornekler:
  python run.py                  # Bugunku batchi calistir
  python run.py --continuous     # Surekli calis (her gun)
  python run.py --test           # Tek video test et
  python run.py --once           # Sadece bugunku batch, kapan
  python run.py --type komik     # Belirli tipte tek video uret
        """,
    )
    parser.add_argument("--test",       action="store_true", help="Tek video uret (pipeline testi)")
    parser.add_argument("--continuous", action="store_true", help="Surekli calis (her gun)")
    parser.add_argument("--once",       action="store_true", help="Bugunku batchi calistir, kapat")
    parser.add_argument("--type",       type=str,            help="Icerik tipi: komik/duygusal/motivasyon/dramatik")
    parser.add_argument("--no-video",   action="store_true", help="Gorsel uretimi atla (sadece ses+senaryo)")
    args = parser.parse_args()

    setup_logging()

    # -- Banner --
    logger.info("=" * 52)
    logger.info("   YouTube Shorts Otomasyon - Odysseus Stack")
    logger.info("   NewsAPI -> GPT-4o -> ElevenLabs -> JSON2Video")
    logger.info("=" * 52)
    logger.info(f"   Dil: {cfg.LANGUAGE}  |  Gunluk: {cfg.DAILY_VIDEO_COUNT} video  |  Aralik: {cfg.INTERVAL_MINUTES}dk")
    logger.info(f"   Cikti: {cfg.OUTPUT_DIR}\n")

    # -- API Kontrolu --
    if not check_api_keys():
        logger.error("\n[X] Eksik API anahtari! .env dosyasini kontrol et.")
        sys.exit(1)

    # -- Wrapper fonksiyon (scheduler icin) --
    def produce_fn(content_config: dict, index: int, total: int) -> Path | None:
        return produce_video(content_config, index, total)

    scheduler = VideoScheduler(produce_video_fn=produce_fn)

    try:
        if args.test:
            # -- Test Modu: tek video --
            content_cfg = cfg.CONTENT_SCHEDULE[0]
            if args.type:
                matches = [c for c in cfg.CONTENT_SCHEDULE if c["type"] == args.type]
                if matches:
                    content_cfg = matches[0]
                else:
                    logger.warning(f"Tip bulunamadi: {args.type}. Ilk tip kullaniliyor.")
            scheduler.run_once(content_cfg, index=1, total=1)

        elif args.type:
            # -- Belirli tip modu --
            matches = [c for c in cfg.CONTENT_SCHEDULE if c["type"] == args.type]
            if not matches:
                logger.error(f"Gecersiz tip: {args.type}. Gecerli tipler: komik, duygusal, motivasyon, dramatik")
                sys.exit(1)
            scheduler.run_once(matches[0], index=1, total=1)

        elif args.continuous:
            # -- Surekli Mod --
            scheduler.run_continuous()

        else:
            # -- Varsayilan / --once: Bugunku batch --
            scheduler.run_daily_batch()

    except KeyboardInterrupt:
        logger.info("\n[DURDURULDU] Yarin kaldigin yerden devam et: python run.py")


if __name__ == "__main__":
    main()
