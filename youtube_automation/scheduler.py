"""
scheduler.py — Günlük video üretim döngüsünü yönetir.
Her video arasında cfg.INTERVAL_MINUTES kadar bekler.
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import sys
sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logger = logging.getLogger(__name__)


class VideoScheduler:
    """Günlük video üretim döngüsünü yöneten sınıf - 7/7 tam otomasyon."""

    def __init__(self, produce_video_fn: Callable):
        """
        Args:
            produce_video_fn: Her video için çağrılacak fonksiyon.
                              (content_config, index, total) argümanları alır.
        """
        self.produce_video = produce_video_fn
        self.daily_count   = cfg.DAILY_VIDEO_COUNT
        self.interval_min  = cfg.INTERVAL_MINUTES
        self._running      = False
        self._seven_days_active = True  # 7/7 modu aktif

    def run_daily_batch(self) -> dict:
        """
        Günlük video batch'ini çalıştırır.
        Tüm videoları sırayla üretir, aralarında bekleme yapar.

        Returns:
            {"produced": int, "failed": int, "videos": [Path]}
        """
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"\n{'='*60}")
        logger.info(f" Günlük batch başladı: {today}")
        logger.info(f"   {self.daily_count} video · {self.interval_min}dk aralık")
        logger.info(f"{'='*60}\n")

        schedule = cfg.CONTENT_SCHEDULE[:self.daily_count]
        results  = {"produced": 0, "failed": 0, "videos": []}

        for i, content_cfg in enumerate(schedule):
            video_num = i + 1
            total     = len(schedule)

            logger.info(f"\n[{video_num}/{total}] Video hazırlanıyor: {content_cfg['label']}")
            logger.info(f"{''*40}")

            try:
                video_path = self.produce_video(
                    content_config=content_cfg,
                    index=video_num,
                    total=total,
                )

                if video_path:
                    results["produced"] += 1
                    results["videos"].append(video_path)
                    logger.info(f" [{video_num}/{total}] Başarılı: {Path(video_path).name}")
                else:
                    results["failed"] += 1
                    logger.error(f" [{video_num}/{total}] Başarısız: {content_cfg['label']}")

            except Exception as e:
                results["failed"] += 1
                logger.exception(f" [{video_num}/{total}] Hata: {e}")

            # Son video değilse bekle
            if i < len(schedule) - 1:
                next_time = datetime.now() + timedelta(minutes=self.interval_min)
                logger.info(f"\n⏰ Sonraki video: {self.interval_min} dakika sonra ({next_time.strftime('%H:%M')})")
                self._wait_with_countdown(self.interval_min * 60)

        # Günlük özet
        logger.info(f"\n{'='*60}")
        logger.info(f" Günlük Özet — {today}")
        logger.info(f"    Başarılı : {results['produced']}")
        logger.info(f"    Başarısız: {results['failed']}")
        logger.info(f"    Videolar : {cfg.OUTPUT_DIR}")
        logger.info(f"{'='*60}\n")

        return results

    def run_once(self, content_config: dict, index: int = 1, total: int = 1) -> None:
        """Tek video üretir (test modu için)."""
        logger.info(" Tek video modu (--test)")
        video_path = self.produce_video(
            content_config=content_config,
            index=index,
            total=total,
        )
        if video_path:
            logger.info(f" Test videosu hazır: {video_path}")
        else:
            logger.error(" Test videosu üretilemedi")

    def run_continuous(self) -> None:
        """
        Sürekli mod: Her gün batch çalıştırır (7/7 tam otomasyon).
        Haftanın her günü çalışır, gün sonunda bir sonraki güne kadar bekler.
        """
        self._running = True
        logger.info(" 🚀 7/7 Tam Otomasyon Modu Aktif (Ctrl+C ile durdur)")
        logger.info("    Haftanın her günü otomatik video üretimi")

        while self._running:
            try:
                # Günlük batch'i çalıştır
                self.run_daily_batch()

                # Bir sonraki güne kadar bekle
                if self._running:
                    now = datetime.now()
                    tomorrow = (now + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    wait_sec = int((tomorrow - now).total_seconds())
                    wait_hr = wait_sec // 3600
                    wait_min = (wait_sec % 3600) // 60

                    day_name = tomorrow.strftime("%A")
                    logger.info(f" ⏰ {day_name} günü için bekleniyor: {wait_hr}sa {wait_min}dk")
                    logger.info("    7/7 modu aktif - haftanın her günü çalışacak")
                    self._wait_with_countdown(wait_sec, log_interval=3600)  # Saatte bir log

            except KeyboardInterrupt:
                logger.info("\n ⏹️  Durduruldu (Ctrl+C)")
                self._running = False
                break
            except Exception as e:
                logger.exception(f"Batch hatası: {e}")
                logger.info(" ⚠️  60 saniye sonra tekrar denenecek...")
                time.sleep(60)

    def stop(self) -> None:
        """Sürekli modu durdurur."""
        self._running = False

    def _wait_with_countdown(self, total_seconds: int, log_interval: int = 300) -> None:
        """Belirtilen süre kadar bekler, periyodik log yazar."""
        if total_seconds <= 0:
            return

        elapsed = 0
        while elapsed < total_seconds and self._running:
            sleep_chunk = min(log_interval, total_seconds - elapsed)
            time.sleep(sleep_chunk)
            elapsed += sleep_chunk

            remaining = total_seconds - elapsed
            if remaining > 0 and elapsed % log_interval == 0:
                rem_min = remaining // 60
                logger.debug(f"  ⏰ {rem_min} dakika kaldı...")


def create_scheduler(produce_fn: Callable) -> VideoScheduler:
    """VideoScheduler instance oluşturur."""
    return VideoScheduler(produce_video_fn=produce_fn)
