"""
overlay_effects.py — Dinamik ekran yazıları ve overlay animasyonları.
Title cards, hook metinleri, istatistik kutuları, emoji, arrow, highlight efektleri.
"""

import logging
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


class OverlayEffectsGenerator:
    """
    Dinamik overlay efektleri oluşturucu.
    - Title cards
    - Hook metinleri
    - İstatistik kutuları
    - Çerçeve efektleri
    """

    def __init__(self):
        self.color_schemes = {
            "komik": {
                "primary": "#FFD700",      # Altın
                "secondary": "#FF6B6B",    # Kırmızı
                "accent": "#FF69B4",       # Pembe
                "bg": "#1a1a2e",          # Koyu mavi
                "gradient_start": "#2d1f3d",
                "gradient_end": "#1a1a2e",
            },
            "kedi": {
                "primary": "#FF69B4",      # Pembe
                "secondary": "#FFB6C1",    # Açık pembe
                "accent": "#FF1493",       # Derin pembe
                "bg": "#2d1f2f",           # Mor-pembe
                "gradient_start": "#4a2f4f",
                "gradient_end": "#2d1f2f",
            },
            "tarih": {
                "primary": "#DAA520",      # Altın
                "secondary": "#8B4513",    # Kahverengi
                "accent": "#CD853F",       # Peru
                "bg": "#1a1510",           # Koyu kahve
                "gradient_start": "#2a2520",
                "gradient_end": "#1a1510",
            },
            "viral": {
                "primary": "#FF4500",      # Turuncu-kırmızı
                "secondary": "#FF1493",    # Derin pembe
                "accent": "#FF6347",       # Domates
                "bg": "#1a0a0a",           # Siyah
                "gradient_start": "#2a1a1a",
                "gradient_end": "#1a0a0a",
            },
            "futbol": {
                "primary": "#32CD32",      # Yeşil
                "secondary": "#FFFFFF",    # Beyaz
                "accent": "#228B22",       # Orman yeşili
                "bg": "#0a1a0a",           # Koyu yeşil
                "gradient_start": "#1a2a1a",
                "gradient_end": "#0a1a0a",
            },
            "duygusal": {
                "primary": "#FF69B4",      # Pembe
                "secondary": "#4169E1",    # Kral mavisi
                "accent": "#1E90FF",       # Dodger mavisi
                "bg": "#1a1020",           # Koyu mavi
                "gradient_start": "#2a2030",
                "gradient_end": "#1a1020",
            },
            "motivasyon": {
                "primary": "#FFD700",      # Altın
                "secondary": "#FF8C00",    # Koyu turuncu
                "accent": "#FFA500",      # Turuncu
                "bg": "#1a1a0a",           # Koyu siyah
                "gradient_start": "#2a2a1a",
                "gradient_end": "#1a1a0a",
            },
            "dramatik": {
                "primary": "#DC143C",      # Koyu kırmızı
                "secondary": "#8B0000",    # Koyu kırmızı
                "accent": "#B22222",       # Ateş tuğlası
                "bg": "#0a0a0a",           # Siyah
                "gradient_start": "#1a0a0a",
                "gradient_end": "#0a0a0a",
            },
        }

    def generate_title_card(
        self,
        title: str,
        hook: str,
        content_type: str = "komik",
        width: int = 720,
        height: int = 1280,
    ) -> Path:
        """
        Dikkat çekici title card görseli oluşturur.

        Args:
            title: Ana başlık
            hook: İlk satır hook metni
            content_type: İçerik tipi (renk şeması için)
            width: Görsel genişliği
            height: Görsel yüksekliği

        Returns:
            Title card görsel yolu
        """
        colors = self.color_schemes.get(content_type, self.color_schemes["komik"])

        # Görsel oluştur
        img = Image.new("RGB", (width, height), color=colors["bg"])
        draw = ImageDraw.Draw(img)

        # Gradient arka plan
        self._draw_gradient(draw, width, height, colors["gradient_start"], colors["gradient_end"])

        # Dekoratif çerçeve
        self._draw_decorative_frame(draw, width, height, colors["primary"])

        # Hook metni (üstte, büyük ve dikkat çekici)
        if hook:
            self._draw_centered_text(
                draw, hook.upper(),
                y_pos=height * 0.25,
                font_size=42,
                color=colors["primary"],
                shadow=True,
                max_width=width - 80,
            )

        # Ana başlık (ortada)
        if title:
            self._draw_centered_text(
                draw, title,
                y_pos=height * 0.5,
                font_size=36,
                color=colors["secondary"],
                shadow=True,
                max_width=width - 80,
            )

        # Alt bilgi kaldırıldı (sağ alt fragment istenmiyor)

        # Kaydet
        output_path = cfg.TEMP_DIR / f"title_card_{content_type}_{random.randint(1000, 9999)}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)

        logger.info(f"✓ Title card oluşturuldu: {output_path.name}")
        return output_path

    def generate_statistic_box(
        self,
        label: str,
        value: str,
        content_type: str = "komik",
        width: int = 600,
        height: int = 200,
    ) -> Path:
        """
        İstatistik kutusu görseli oluşturur.

        Args:
            label: İstatistik etiketi
            value: İstatistik değeri
            content_type: İçerik tipi
            width: Kutu genişliği
            height: Kutu yüksekliği

        Returns:
            İstatistik kutusu görsel yolu
        """
        colors = self.color_schemes.get(content_type, self.color_schemes["komik"])

        # Görsel oluştur
        img = Image.new("RGB", (width, height), color=colors["bg"])
        draw = ImageDraw.Draw(img)

        # Gradient arka plan
        self._draw_gradient(draw, width, height, colors["gradient_start"], colors["gradient_end"])

        # Kenarlık
        border_color = colors["primary"]
        draw.rectangle([(10, 10), (width - 10, height - 10)], outline=border_color, width=3)
        draw.rectangle([(15, 15), (width - 15, height - 15)], outline=colors["secondary"], width=1)

        # Label (üstte)
        self._draw_centered_text(
            draw, label.upper(),
            y_pos=height * 0.3,
            font_size=28,
            color=colors["secondary"],
            shadow=True,
            max_width=width - 40,
        )

        # Value (ortada, büyük)
        self._draw_centered_text(
            draw, value,
            y_pos=height * 0.7,
            font_size=48,
            color=colors["primary"],
            shadow=True,
            max_width=width - 40,
        )

        # Kaydet
        output_path = cfg.TEMP_DIR / f"stat_box_{content_type}_{random.randint(1000, 9999)}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)

        logger.info(f"✓ İstatistik kutusu oluşturuldu: {output_path.name}")
        return output_path

    def generate_highlight_overlay(
        self,
        text: str,
        content_type: str = "komik",
        width: int = 500,
        height: int = 150,
    ) -> Path:
        """
        Highlight overlay görseli oluşturur (vurgulu metinler için).

        Args:
            text: Vurgulanacak metin
            content_type: İçerik tipi
            width: Overlay genişliği
            height: Overlay yüksekliği

        Returns:
            Highlight overlay görsel yolu
        """
        colors = self.color_schemes.get(content_type, self.color_schemes["komik"])

        # Görsel oluştur (transparent background için RGBA)
        img = Image.new("RGBA", (width, height), color=(0, 0, 0, 180))  # Yarı saydam siyah
        draw = ImageDraw.Draw(img)

        # Gradient kenarlık
        self._draw_gradient_border(draw, width, height, colors["primary"], colors["secondary"])

        # Metin
        self._draw_centered_text(
            draw, text.upper(),
            y_pos=height * 0.5,
            font_size=32,
            color=colors["primary"],
            shadow=True,
            max_width=width - 40,
        )

        # Kaydet
        output_path = cfg.TEMP_DIR / f"highlight_{content_type}_{random.randint(1000, 9999)}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)

        logger.info(f"✓ Highlight overlay oluşturuldu: {output_path.name}")
        return output_path

    def _draw_gradient(self, draw, width, height, start_color, end_color):
        """Dikey gradient çizer."""
        start_rgb = self._hex_to_rgb(start_color)
        end_rgb = self._hex_to_rgb(end_color)

        for y in range(height):
            ratio = y / height
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

    def _draw_gradient_border(self, draw, width, height, color1, color2):
        """Gradient kenarlık çizer."""
        color1_rgb = self._hex_to_rgb(color1)
        color2_rgb = self._hex_to_rgb(color2)

        # Üstten aşağı gradient
        for i in range(10):
            ratio = i / 10
            r = int(color1_rgb[0] + (color2_rgb[0] - color1_rgb[0]) * ratio)
            g = int(color1_rgb[1] + (color2_rgb[1] - color1_rgb[1]) * ratio)
            b = int(color1_rgb[2] + (color2_rgb[2] - color1_rgb[2]) * ratio)
            draw.rectangle([(i, i), (width - i, height - i)], outline=(r, g, b), width=1)

    def _draw_decorative_frame(self, draw, width, height, color):
        """Dekoratif çerçeve çizer."""
        color_rgb = self._hex_to_rgb(color)

        # Ana çerçeve
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=color_rgb, width=3)
        draw.rectangle([(25, 25), (width - 25, height - 25)], outline=color_rgb, width=1)

        # Köşe süslemeleri
        corner_size = 40
        for x, y in [(20, 20), (width - 20, 20), (20, height - 20), (width - 20, height - 20)]:
            draw.rectangle([(x, y), (x + corner_size, y + corner_size)], outline=color_rgb, width=2)

    def _draw_centered_text(
        self,
        draw,
        text: str,
        y_pos: float,
        font_size: int,
        color: str,
        shadow: bool = False,
        max_width: int = 600,
    ):
        """Ortalanmış metin çizer (satır kaydırma desteği ile)."""
        color_rgb = self._hex_to_rgb(color)

        # Font yükle (basit fallback)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Metni satırlara böl
        lines = textwrap.wrap(text, width=max_width // (font_size // 2))

        # Her satırı çiz
        total_height = len(lines) * font_size * 1.2
        start_y = y_pos - total_height / 2

        for i, line in enumerate(lines):
            line_y = start_y + i * font_size * 1.2

            # Shadow
            if shadow:
                draw.text((10, line_y + 2), line, font=font, fill=(0, 0, 0, 128))

            # Ana metin
            draw.text((10, line_y), line, font=font, fill=color_rgb)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Hex renk kodunu RGB'ye dönüştürür."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _get_content_emoji(self, content_type: str) -> str:
        """İçerik tipine göre emoji döndürür."""
        emoji_map = {
            "komik": "😂",
            "kedi": "🐱",
            "tarih": "📜",
            "viral": "🔥",
            "futbol": "⚽",
            "duygusal": "❤️",
            "motivasyon": "💪",
            "dramatik": "🎭",
        }
        return emoji_map.get(content_type, "✨")


def generate_overlay_assets(
    script: dict,
    content_type: str = "komik"
) -> Dict[str, Path]:
    """
    Script'ten overlay görselleri oluşturur.

    Args:
        script: Senaryo verisi
        content_type: İçerik tipi

    Returns:
        Overlay görselleri dict (title_card, highlight_box, stat_box)
    """
    generator = OverlayEffectsGenerator()
    overlays = {}

    try:
        # Title card
        title = script.get("title", "")
        hook = script.get("hook", "")
        if title or hook:
            title_card = generator.generate_title_card(title, hook, content_type)
            overlays["title_card"] = title_card

        # Highlight box (ilk sahne için)
        scenes = script.get("scenes", [])
        if scenes:
            first_scene_text = scenes[0].get("narration_chunk", "")
            if first_scene_text:
                # İlk 3 kelimeyi highlight yap
                words = first_scene_text.split()[:3]
                highlight_text = " ".join(words)
                highlight_box = generator.generate_highlight_overlay(highlight_text, content_type)
                overlays["highlight_box"] = highlight_box

        # İstatistik kutusu (eğer istatistik varsa)
        stats = script.get("statistics", {})
        if stats:
            label = list(stats.keys())[0]
            value = str(list(stats.values())[0])
            stat_box = generator.generate_statistic_box(label, value, content_type)
            overlays["stat_box"] = stat_box

        logger.info(f"✓ {len(overlays)} overlay görseli oluşturuldu")
        return overlays

    except Exception as e:
        logger.error(f"Overlay oluşturma hatası: {e}")
        return overlays


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test
    generator = OverlayEffectsGenerator()

    # Title card test
    title_card = generator.generate_title_card(
        "İnanılmaz Bir Hikaye",
        "BUNU DUYDUN MU?",
        "komik"
    )
    print(f"Title card: {title_card}")

    # İstatistik kutusu test
    stat_box = generator.generate_statistic_box(
        "Görüntülenme",
        "1.2M",
        "viral"
    )
    print(f"Stat box: {stat_box}")