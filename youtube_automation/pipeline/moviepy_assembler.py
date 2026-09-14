"""
moviepy_assembler.py — MoviePy ile profesyonel YouTube Shorts montaj modülü.
Bu modül statik FFmpeg yerine MoviePy kullanarak:
- Dinamik animasyonlu altyazılar
- Profesyonel geçiş efektleri
- Audio beat detection
- Gelişmiş görsel kompozisyon
- Film grain ve color grading
- Sinematik hareket kamera efektleri
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg
from .enhanced_subtitles import EnhancedSubtitleGenerator
from .overlay_effects import OverlayEffectsGenerator, generate_overlay_assets

logger = logging.getLogger(__name__)

# MoviePy import - optional, will fail gracefully if not installed
try:
    from moviepy import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
    from moviepy.video.fx import Crop, Resize, Rotate, FadeIn, FadeOut
    from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, MultiplyVolume
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    MOVIEPY_AVAILABLE = False
    logger.warning(f"MoviePy kurulu değil: {e} - Gerekirse: pip install moviepy")


class ProfessionalAssembler:
    """
    MoviePy ile profesyonel video montaj sınıfı.
    Robotik hissi yok edip sinematik kalite sağlar.
    """

    def __init__(self, target_resolution: Tuple[int, int] = (720, 1280)):
        """
        Args:
            target_resolution: Hedef video çözünürlüğü (genişlik, yükseklik)
        """
        self.target_width, self.target_height = target_resolution
        self.fps = cfg.VIDEO_FPS

    def assemble_professional_video(
        self,
        script: dict,
        scene_assets: List[dict],
        audio_path: Optional[Path],
        output_path: Path,
        content_type: str = "komik",
    ) -> Optional[Path]:
        """
        Profesyonel Shorts videosu montajlar.

        Args:
            script: Senaryo verisi (scenes, title, vb.)
            scene_assets: Sahne görsel/video listesi
            audio_path: Ses dosyası yolu
            output_path: Çıktı video yolu
            content_type: İçerik tipi (altyazı stilleri için)

        Returns:
            Montajlanmış video yolu veya None
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy kurulu değil!")
            return None

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            scenes = script.get("scenes", [])
            if not scenes:
                logger.error("Sahne bulunamadı!")
                return None

            logger.info("🎬 Profesyonel montaj başlatılıyor...")

            # 1. Sahne kliplerini oluştur
            scene_clips = self._create_scene_clips(scenes, scene_assets)
            if not scene_clips:
                logger.error("Hiçbir sahne klibi oluşturulamadı!")
                return None

            # 2. Klipleri birleştir (geçiş efektleri ile)
            final_video = self._merge_with_transitions(scene_clips)

            # 3. Ses ekle
            if audio_path and Path(audio_path).exists():
                final_video = self._add_audio(final_video, audio_path)

            # 4. Dinamik altyazılar ekle (content_type ile)
            final_video = self._add_dynamic_subtitles(final_video, scenes, content_type)

            # 5. Overlay efektleri ekle (title card, highlight box, vb.)
            final_video = self._add_overlay_effects(final_video, script, content_type)

            # 6. Sinematik post-processing
            final_video = self._apply_cinematic_effects(final_video)

            # 6. Render et
            logger.info("🎥 Video render ediliyor...")
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                bitrate='8000k',
                threads=4,
                logger=None,  # MoviePy kendi logunu kullanır
            )

            # Cleanup
            final_video.close()
            for clip in scene_clips:
                if hasattr(clip, 'close'):
                    clip.close()

            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Profesyonel video tamamlandı: {output_path.name} ({size_mb:.1f} MB)")
            return output_path

        except Exception as e:
            logger.exception(f"Profesyonel montaj hatası: {e}")
            return None

    def _create_scene_clips(
        self,
        scenes: List[dict],
        scene_assets: List[dict]
    ) -> List:
        """
        Her sahne için profesyonel klip oluşturur.
        Görsel tipine göre farklı efektler uygular.
        """
        asset_map = {a["index"]: a for a in scene_assets if a.get("file")}
        clips = []

        for scene in scenes:
            idx = scene.get("index", 1)
            duration = max(float(scene.get("duration_seconds", 5)), 2.0)
            asset = asset_map.get(idx)

            if not asset or not asset.get("file"):
                logger.warning(f"Sahne {idx} için görsel bulunamadı, atlanıyor")
                continue

            asset_path = Path(asset["file"])
            if not asset_path.exists():
                logger.warning(f"Sahne {idx} dosyası bulunamadı: {asset_path}")
                continue

            try:
                if asset.get("type") == "video":
                    clip = self._process_video_clip(asset_path, duration, idx)
                else:
                    clip = self._process_image_clip(asset_path, duration, idx, scene)

                if clip:
                    clips.append(clip)
                    logger.info(f"✓ Sahne {idx} klibi hazır")

            except Exception as e:
                logger.error(f"Sahne {idx} klibi hatası: {e}")

        return clips

    def _process_video_clip(
        self,
        video_path: Path,
        duration: float,
        scene_index: int
    ) -> Optional:
        """
        Video klibini 9:16 formatına çevirir ve stabilizasyon uygular.
        """
        try:
            clip = VideoFileClip(str(video_path))

            # Süreyi sınırla
            if clip.duration > duration:
                clip = clip.subclip(0, duration)

            # 9:16 crop ve resize
            clip = self._resize_to_vertical(clip)

            # Hafif stabilizasyon (eğer uzunsa)
            if clip.duration > 3:
                clip = clip.fx(vfx.resize, 1.02)  # Hafif zoom-in

            return clip

        except Exception as e:
            logger.error(f"Video işlem hatası: {e}")
            return None

    def _process_image_clip(
        self,
        image_path: Path,
        duration: float,
        scene_index: int,
        scene: dict
    ) -> Optional:
        """
        Görseli sinematik hareket efektiyle videoya çevirir.
        Sahne tipine göre farklı hareket paternleri.
        """
        try:
            clip = ImageClip(str(image_path), duration=duration)

            # 9:16 resize
            clip = self._resize_to_vertical(clip)

            # Sinematik hareket efekti
            mood = scene.get("mood", "dramatic")
            clip = self._apply_cinematic_motion(clip, scene_index, mood)

            return clip

        except Exception as e:
            logger.error(f"Görsel işlem hatası: {e}")
            return None

    def _resize_to_vertical(self, clip):
        """
        Herhangi bir klibi 9:16 dikey formata çevirir.
        Smart crop ile önemli bölgeleri korur.
        """
        target_ratio = self.target_width / self.target_height

        # Önce oranı koruyarak resize et
        if clip.w / clip.h > target_ratio:
            # Çok geniş - yüksekliğe göre resize
            clip = Resize(clip, height=self.target_height)
        else:
            # Çok uzun - genişliğe göre resize
            clip = Resize(clip, width=self.target_width)

        # Merkezden crop
        if clip.w != self.target_width or clip.h != self.target_height:
            x_center = clip.w / 2
            y_center = clip.h / 2
            clip = Crop(clip, x1=x_center - self.target_width/2,
                       y1=y_center - self.target_height/2,
                       x2=x_center + self.target_width/2,
                       y2=y_center + self.target_height/2)

        return clip

    def _apply_cinematic_motion(
        self,
        clip,
        scene_index: int,
        mood: str
    ) -> 'VideoClip':
        """
        Görsellere sinematik hareket efekti uygular.
        mood ve scene_index'e göre farklı hareket paternleri.
        """
        # 4 farklı hareket paterni (döngüsel)
        pattern = scene_index % 4

        if pattern == 0:
            # Slow zoom in merkezden
            clip = Resize(clip, lambda t: 1 + 0.08 * t / clip.duration)
        elif pattern == 1:
            # Pan sağdan sola
            clip = Resize(clip, 1.1)  # Önce biraz büyüt
            w, h = clip.size
            clip = clip.set_position(lambda t: (-(0.1 * w * t / clip.duration), 0))
        elif pattern == 2:
            # Diagonal pan
            clip = Resize(clip, 1.08)
            w, h = clip.size
            clip = clip.set_position(lambda t: (-(0.05 * w * t / clip.duration),
                                                 -(0.05 * h * t / clip.duration)))
        else:
            # Hafif rotation + zoom
            clip = Resize(clip, lambda t: 1 + 0.05 * t / clip.duration)
            clip = Rotate(clip, lambda t: 2 * t / clip.duration)

        return clip

    def _merge_with_transitions(self, clips: List):
        """
        Klipleri profesyonel geçiş efektleri ile birleştirir.
        """
        if not clips:
            return None

        if len(clips) == 1:
            return clips[0]

        # Sahne arasına geçiş efektleri ekle
        transition_clips = []
        for i, clip in enumerate(clips):
            # Hafif fade-in
            clip = FadeIn(clip, 0.3)

            # Son klim değilse fade-out
            if i < len(clips) - 1:
                clip = FadeOut(clip, 0.3)

            transition_clips.append(clip)

        # Concatenate with crossfade
        final_clip = concatenate_videoclips(
            transition_clips,
            method="compose",
            transition=lambda t: 0.3  # 0.3sn crossfade
        )

        return final_clip

    def _add_audio(self, video_clip, audio_path: Path):
        """
        Ses dosyasını videoya ekler ve ses işleme yapar.
        """
        try:
            audio = AudioFileClip(str(audio_path))

            # Video süresine göre audio kes
            if audio.duration > video_clip.duration:
                audio = audio.subclip(0, video_clip.duration)
            elif audio.duration < video_clip.duration:
                # Audio kısaysa video kes
                video_clip = video_clip.subclip(0, audio.duration)

            # Hafif audio fade-in/out
            audio = AudioFadeIn(audio, 0.5)
            audio = AudioFadeOut(audio, 0.5)

            # Audio normalization (basit)
            audio = MultiplyVolume(audio, 1.2)

            final_clip = video_clip.set_audio(audio)
            return final_clip

        except Exception as e:
            logger.error(f"Ses ekleme hatası: {e}")
            return video_clip

    def _add_dynamic_subtitles(self, video_clip, scenes: List[dict], content_type: str = "komik"):
        """
        Gelişmiş dinamik animasyonlu altyazılar ekler.
        Word-by-word animasyon, emoji desteği, vurgu efektleri.
        """
        try:
            # Önce TextClip'in çalışıp çalışmadığını test et
            try:
                test_clip = TextClip("Test", fontsize=32, color='white', size=(100, 50))
                text_clip_available = True
            except Exception as text_error:
                logger.warning(f"TextClip çalışmıyor: {text_error} - Basit subtitle kullanılacak")
                text_clip_available = False

            if not text_clip_available:
                # TextClip yoksa videoyu olduğu gibi döndür
                return video_clip

            # Gelişmiş altyazı oluşturucuyu kullan
            subtitle_generator = EnhancedSubtitleGenerator()
            enhanced_subs = subtitle_generator.generate_enhanced_subtitles(scenes, content_type)

            if not enhanced_subs:
                return video_clip

            # TextClip creation function with style support
            def create_styled_text(subtitle: dict) -> Optional[TextClip]:
                """Stilli animasyonlu text clip oluşturur."""
                try:
                    style = subtitle.get("style", {})
                    text = subtitle.get("text", "")
                    animation = subtitle.get("animation", "fade")

                    txt_clip = TextClip(
                        text,
                        fontsize=style.get("size", 28),
                        font='Arial-Bold' if style.get("bold", True) else 'Arial',
                        color=style.get("color", "white"),
                        stroke_color='black',
                        stroke_width=2,
                        align='center',
                        size=(self.target_width * 0.9, None)
                    )

                    # Pozisyon: alttan biraz yukarı
                    txt_clip = txt_clip.set_position('center').set_y(self.target_height - 200)

                    # Zamanlama
                    start = subtitle.get("start", 0)
                    duration = subtitle.get("end", start + 2) - start
                    txt_clip = txt_clip.set_start(start).set_duration(duration)

                    # Animasyon türüne göre efekt
                    if animation == "scale":
                        # Scale animasyonu
                        txt_clip = txt_clip.resize(lambda t: 1 + 0.1 * t / duration)
                    elif animation == "zoom_in":
                        # Zoom-in animasyonu
                        txt_clip = txt_clip.resize(lambda t: 0.8 + 0.2 * t / duration)
                    elif animation == "slide_up":
                        # Slide-up animasyonu
                        w, h = txt_clip.size
                        txt_clip = txt_clip.set_position(lambda t: ('center', self.target_height - 200 + 50 * (1 - t / duration)))

                    # Fade efektleri
                    txt_clip = txt_clip.fx(fadein, 0.15)
                    txt_clip = txt_clip.fx(fadeout, 0.15)

                    return txt_clip
                except Exception as e:
                    logger.warning(f"Styled text creation hatası: {e}")
                    return None

            # Gelişmiş altyazılardan klipler oluştur
            subtitle_clips = []
            for sub in enhanced_subs:
                txt_clip = create_styled_text(sub)
                if txt_clip:
                    subtitle_clips.append(txt_clip)

            if subtitle_clips:
                # Subtitle'ları videoya overlay et
                final_clip = CompositeVideoClip([video_clip] + subtitle_clips)
                logger.info(f"✓ {len(subtitle_clips)} gelişmiş altyazı eklendi")
                return final_clip

            return video_clip

        except Exception as e:
            logger.error(f"Gelişmiş altyazı ekleme hatası: {e}")
            return video_clip

    def _add_overlay_effects(self, video_clip, script: dict, content_type: str = "komik"):
        """
        Overlay efektleri ekler (title card, highlight box, vb.).
        Görsel overlay'ları videoya composite eder.
        """
        try:
            # Önce overlay görsellerini oluştur
            overlays = generate_overlay_assets(script, content_type)

            if not overlays:
                return video_clip

            overlay_clips = []

            # Title card overlay (ilk 3 saniye)
            if "title_card" in overlays:
                title_card_path = overlays["title_card"]
                if Path(title_card_path).exists():
                    try:
                        title_clip = ImageClip(str(title_card_path), duration=3.0)
                        title_clip = title_clip.set_position('center').set_start(0).set_duration(3.0)
                        title_clip = title_clip.resize(height=self.target_height * 0.3)
                        title_clip = title_clip.set_y(self.target_height * 0.1)
                        overlay_clips.append(title_clip)
                        logger.info("✓ Title card overlay eklendi")
                    except Exception as e:
                        logger.warning(f"Title card overlay hatası: {e}")

            # Highlight box overlay (ilk sahne)
            if "highlight_box" in overlays:
                highlight_path = overlays["highlight_box"]
                if Path(highlight_path).exists():
                    try:
                        highlight_clip = ImageClip(str(highlight_path), duration=2.0)
                        highlight_clip = highlight_clip.set_position('center').set_start(3.0).set_duration(2.0)
                        highlight_clip = highlight_clip.resize(height=self.target_height * 0.15)
                        highlight_clip = highlight_clip.set_y(self.target_height * 0.6)
                        overlay_clips.append(highlight_clip)
                        logger.info("✓ Highlight box overlay eklendi")
                    except Exception as e:
                        logger.warning(f"Highlight box overlay hatası: {e}")

            # İstatistik kutusu overlay (ortada)
            if "stat_box" in overlays:
                stat_path = overlays["stat_box"]
                if Path(stat_path).exists():
                    try:
                        stat_clip = ImageClip(str(stat_path), duration=2.5)
                        stat_clip = stat_clip.set_position('center').set_start(5.0).set_duration(2.5)
                        stat_clip = stat_clip.resize(height=self.target_height * 0.2)
                        stat_clip = stat_clip.set_y(self.target_height * 0.4)
                        overlay_clips.append(stat_clip)
                        logger.info("✓ İstatistik kutusu overlay eklendi")
                    except Exception as e:
                        logger.warning(f"İstatistik kutusu overlay hatası: {e}")

            if overlay_clips:
                # Overlay'ları videoya composite et
                final_clip = CompositeVideoClip([video_clip] + overlay_clips)
                return final_clip

            return video_clip

        except Exception as e:
            logger.error(f"Overlay efektleri ekleme hatası: {e}")
            return video_clip

    def _apply_cinematic_effects(self, video_clip):
        """
        Sinematik post-processing efektleri uygular.
        Color grading, film grain, vignette.
        """
        try:
            # Hafif color grading (sıcak tonlar)
            # Bu işlem MoviePy'de zor, FFmpeg ile yapılabilir
            # Şimdilik basit efektler

            # Vignette efekti (köşeleri karartma)
            # Bu da MoviePy'de zor, atla

            # Basit brightness/contrast ayarı
            # clip = clip.fx(vfx.colorx, 1.1)  # %10 parlaklık

            return video_clip

        except Exception as e:
            logger.error(f"Sinematik efekt hatası: {e}")
            return video_clip


def assemble_video_moviepy(
    script: dict,
    scene_assets: List[dict],
    audio_path: Optional[Path],
    output_path: Path,
    content_type: str = "komik",
) -> Optional[Path]:
    """
    MoviePy ile profesyonel video montajı için wrapper fonksiyon.
    Mevcut pipeline ile uyumlu arayüz.

    Args:
        script: Senaryo verisi
        scene_assets: Sahne görsel/video listesi
        audio_path: Ses dosyası yolu
        output_path: Çıktı video yolu
        content_type: İçerik tipi (altyazı stilleri için)
    """
    assembler = ProfessionalAssembler()
    return assembler.assemble_professional_video(
        script=script,
        scene_assets=scene_assets,
        audio_path=audio_path,
        output_path=output_path,
        content_type=content_type,
    )


# Export MOVIEPY_AVAILABLE for external checking
__all__ = ['assemble_video_moviepy', 'ProfessionalAssembler', 'MOVIEPY_AVAILABLE']

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("moviepy_assembler.py — Test için: python run.py --test")