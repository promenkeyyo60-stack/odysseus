"""
enhanced_subtitles.py — Gelişmiş animasyonlu altyazı sistemi.
Word-by-word animasyon, emoji desteği, vurgu efektleri, dinamik renkler.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
import random

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


# Emoji haritası - duygulara göre otomatik emoji ekle
EMOJI_MAP = {
    "komik": ["😂", "🤣", "😆", "😄", "🎭", "🎪"],
    "kedi": ["🐱", "😺", "😸", "🐈", "🙀", "😻"],
    "tarih": ["📜", "🏛️", "⚔️", "👑", "🗺️", "📚"],
    "viral": ["🔥", "💥", "⚡", "🚀", "💫", "✨"],
    "futbol": ["⚽", "🏆", "🥅", "🎯", "🏟️", "📊"],
    "duygusal": ["❤️", "💔", "😢", "🤗", "🌟", "💝"],
    "motivasyon": ["💪", "🌟", "🔥", "⚡", "🚀", "✨"],
    "dramatik": ["🎭", "⚡", "🔥", "💥", "🌊", "🎬"],
}


class EnhancedSubtitleGenerator:
    """
    Gelişmiş altyazı oluşturucu.
    - Word-by-word animasyon
    - Emoji desteği
    - Dinamik renkler
    - Vurgu efektleri
    """

    def __init__(self):
        self.color_schemes = {
            "komik": {"primary": "#FFD700", "secondary": "#FF6B6B", "bg": "#1a1a2e"},
            "kedi": {"primary": "#FF69B4", "secondary": "#FFB6C1", "bg": "#2d1f2f"},
            "tarih": {"primary": "#DAA520", "secondary": "#8B4513", "bg": "#1a1510"},
            "viral": {"primary": "#FF4500", "secondary": "#FF1493", "bg": "#1a0a0a"},
            "futbol": {"primary": "#32CD32", "secondary": "#FFFFFF", "bg": "#0a1a0a"},
            "duygusal": {"primary": "#FF69B4", "secondary": "#4169E1", "bg": "#1a1020"},
            "motivasyon": {"primary": "#FFD700", "secondary": "#FF8C00", "bg": "#1a1a0a"},
            "dramatik": {"primary": "#DC143C", "secondary": "#8B0000", "bg": "#0a0a0a"},
        }

    def generate_enhanced_subtitles(
        self,
        scenes: List[dict],
        content_type: str = "komik"
    ) -> List[dict]:
        """
        Gelişmiş altyazı listesi oluşturur.

        Args:
            scenes: Sahne listesi
            content_type: İçerik tipi (renk ve emoji seçimi için)

        Returns:
            Gelişmiş altyazı listesi
        """
        subtitles = []
        current_time = 0.0

        colors = self.color_schemes.get(content_type, self.color_schemes["komik"])
        emojis = EMOJI_MAP.get(content_type, ["✨", "💫", "⭐"])

        for scene in scenes:
            duration = float(scene.get("duration_seconds", 5))
            text = scene.get("narration_chunk", "").strip()

            if not text:
                current_time += duration
                continue

            # Metni satırlara böl (kelime sayısına göre dinamik)
            words = text.split()
            if not words:
                current_time += duration
                continue

            # Her satırda 4-6 kelime (okunabilirlik için)
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if len(current_line) >= 5:  # 5 kelimeden sonra satır atla
                    lines.append(" ".join(current_line))
                    current_line = []
            if current_line:
                lines.append(" ".join(current_line))

            # Her satır için subtitle (daha iyi senkronizasyon)
            if lines:
                line_duration = duration / len(lines)
                for i, line in enumerate(lines):
                    start_time = current_time + i * line_duration
                    end_time = start_time + line_duration - 0.02  # Çok kısa boşluk, senkronizasyon için

                    # İlk satırda emoji ekle
                    emoji = ""
                    if i == 0:
                        emoji = random.choice(emojis)

                    # Vurgu kelimelerini belirle (satır içindeki önemli kelimeler)
                    is_highlight = self._is_line_highlight(line)

                    subtitle = {
                        "start": round(start_time, 3),
                        "end": round(end_time, 3),
                        "text": f"{emoji} {line}" if emoji else line,
                        "style": {
                            "color": colors["secondary"] if is_highlight else colors["primary"],
                            "bold": is_highlight,
                            "italic": not is_highlight,
                            "size": 32 if is_highlight else 28,
                            "bg_color": colors["bg"] if is_highlight else "transparent",
                        },
                        "animation": "scale" if is_highlight else "fade",
                    }

                    subtitles.append(subtitle)

            current_time += duration

        logger.info(f"  {len(subtitles)} gelişmiş altyazı oluşturuldu ({content_type})")
        return subtitles

    def _is_line_highlight(self, line: str) -> bool:
        """
        Vurgulanması gereken satırları belirler.
        Önemli kelimeler, sayılar, kısaltmalar içeren satırlar.
        """
        line_lower = line.lower().strip(".,!?;:")

        # Önemli kelimeler
        important_words = [
            "çok", "en", "ilk", "son", "büyük", "küçük", "güzel", "kötü",
            "inanılmaz", "şaşırtıcı", "mükemmel", "korkunç", "harika",
            "sadece", "asla", "her zaman", "hiç", "belki", "muhtemelen",
            "gerçekten", "kesinlikle", "tamamen", "kesin", "emin",
        ]

        # Sayı kontrolü
        if any(char.isdigit() for char in line):
            return True

        # Uzun satırlar (genelde önemli)
        if len(line) > 35:
            return True

        # Kısaltmalar
        if any(word.upper() == word and len(word) > 2 for word in line.split()):
            return True

        # Önemli kelime içeriyor mu
        if any(word in line_lower for word in important_words):
            return True

        return False

    def generate_srt_from_enhanced(self, subtitles: List[dict]) -> str:
        """
        Gelişmiş altyazılardan SRT formatı oluşturur.
        (FFmpeg için basit SRT - animasyonlar MoviePy ile yapılacak)
        """
        srt_lines = []
        for i, sub in enumerate(subtitles, 1):
            start_time = self._format_srt_time(sub["start"])
            end_time = self._format_srt_time(sub["end"])
            text = sub["text"]

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def _format_srt_time(self, seconds: float) -> str:
        """Saniyeyi SRT zaman damgası formatına dönüştürür."""
        millis = int((seconds - int(seconds)) * 1000)
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def generate_title_card_subtitles(
        self,
        title: str,
        hook: str,
        duration: float = 3.0
    ) -> List[dict]:
        """
        Video başı için title card altyazıları oluşturur.
        Büyük, dikkat çekici başlık ve hook metni.
        """
        subtitles = []

        # Hook metni (ilk 1.5 saniye)
        if hook:
            subtitles.append({
                "start": 0.0,
                "end": 1.5,
                "text": hook.upper(),
                "style": {
                    "color": "#FFD700",
                    "bold": True,
                    "size": 42,
                    "bg_color": "#1a1a2e",
                },
                "animation": "zoom_in",
                "position": "center",
            })

        # Ana başlık (sonraki 1.5 saniye)
        if title:
            subtitles.append({
                "start": 1.5,
                "end": duration,
                "text": title,
                "style": {
                    "color": "#FFFFFF",
                    "bold": True,
                    "size": 36,
                    "bg_color": "transparent",
                },
                "animation": "slide_up",
                "position": "center",
            })

        return subtitles


def generate_enhanced_subtitles_ffmpeg(
    scenes: List[dict],
    content_type: str = "komik"
) -> tuple:
    """
    FFmpeg için gelişmiş altyazı verileri oluşturur.
    (SRT formatı + stil bilgileri)

    Returns:
        (srt_content, style_info) tuple
    """
    generator = EnhancedSubtitleGenerator()
    subtitles = generator.generate_enhanced_subtitles(scenes, content_type)
    srt_content = generator.generate_srt_from_enhanced(subtitles)

    # Stil bilgileri
    colors = generator.color_schemes.get(content_type, generator.color_schemes["komik"])
    style_info = {
        "primary_color": colors["primary"],
        "secondary_color": colors["secondary"],
        "bg_color": colors["bg"],
        "font_size": 28,
        "bold": True,
    }

    return srt_content, style_info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test
    test_scenes = [
        {
            "index": 1,
            "duration_seconds": 5,
            "narration_chunk": "Bu inanılmaz bir hikaye ve kesinlikle duymalısınız."
        }
    ]

    generator = EnhancedSubtitleGenerator()
    subtitles = generator.generate_enhanced_subtitles(test_scenes, "komik")

    for sub in subtitles:
        print(f"{sub['start']:.2f}-{sub['end']:.2f}: {sub['text']} [{sub['animation']}]")