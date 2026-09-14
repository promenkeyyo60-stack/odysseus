"""
visual_templates.py — Konu bazlı dinamik görsel şablonları.
Her içerik tipi için özel görsel prompt'ları ve görsel öğeler.
"""

import logging
import random
from pathlib import Path
from typing import List, Dict, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


class VisualTemplateManager:
    """
    Konu bazlı görsel şablon yöneticisi.
    Her içerik tipi için özel görsel prompt'ları ve öğeler.
    """

    def __init__(self):
        self.templates = {
            "komik": {
                "visual_prompts": [
                    "absurd funny situation with exaggerated expressions, vibrant colors, cartoon-like atmosphere",
                    "unexpected comedic moment with surprised characters, dynamic composition, humorous lighting",
                    "slapstick comedy scene with physical comedy elements, bright and cheerful palette",
                    "ironic situation with deadpan humor, minimalist composition, stark contrast",
                    "viral meme-style visual with bold text placeholders, eye-catching colors, meme aesthetics",
                ],
                "color_palette": ["#FF6B6B", "#FFD700", "#FF69B4", "#4ECDC4", "#45B7D1"],
                "composition": ["dynamic diagonal", "rule of thirds", "center focus", "asymmetric balance"],
                "mood": ["cheerful", "energetic", "playful", "absurd"],
                "camera_angle": ["wide angle", "close-up", "dutch angle", "bird's eye"],
            },
            "kedi": {
                "visual_prompts": [
                    "adorable cat in cute pose, soft natural lighting, pastel colors, heartwarming atmosphere",
                    "playful kitten with toy, dynamic action shot, bright and cheerful, joyful expression",
                    "cat doing something funny or unexpected, humorous feline behavior, entertaining composition",
                    "majestic cat portrait, regal pose, golden hour lighting, elegant and sophisticated",
                    "multiple cats interacting, social feline behavior, warm and cozy atmosphere, domestic setting",
                ],
                "color_palette": ["#FFB6C1", "#FF69B4", "#DDA0DD", "#FFC0CB", "#E6E6FA"],
                "composition": ["intimate close-up", "environmental portrait", "action shot", "candid moment"],
                "mood": ["cute", "playful", "affectionate", "curious"],
                "camera_angle": ["eye level", "low angle", "over shoulder", "macro close-up"],
            },
            "tarih": {
                "visual_prompts": [
                    "ancient historical scene with authentic period details, dramatic lighting, cinematic quality",
                    "mysterious archaeological discovery, underground chamber, ancient artifacts, atmospheric mood",
                    "historical monument or landmark, epic wide shot, golden hour lighting, majestic composition",
                    "ancient manuscript or artifact, detailed close-up, warm library lighting, scholarly atmosphere",
                    "historical battle or event, dramatic composition, smoke and atmosphere, epic scale",
                ],
                "color_palette": ["#DAA520", "#8B4513", "#CD853F", "#DEB887", "#F5DEB3"],
                "composition": ["epic wide shot", "dramatic angle", "symmetrical", "depth layers"],
                "mood": ["mysterious", "epic", "dramatic", "scholarly"],
                "camera_angle": ["low angle", "high angle", "dramatic perspective", "establishing shot"],
            },
            "viral": {
                "visual_prompts": [
                    "trending social media moment, viral aesthetic, bold colors, dynamic composition",
                    "influencer-style shot, modern aesthetic, trendy lighting, contemporary composition",
                    "challenge or trend participation, energetic atmosphere, vibrant colors, action-oriented",
                    "meme-worthy moment, internet culture aesthetic, bold and eye-catching, shareable composition",
                    "current event or news topic, journalistic style, dramatic lighting, newsworthy composition",
                ],
                "color_palette": ["#FF4500", "#FF1493", "#00CED1", "#FFD700", "#1E90FF"],
                "composition": ["dynamic diagonal", "bold center", "asymmetric", "rule of thirds"],
                "mood": ["energetic", "trendy", "bold", "contemporary"],
                "camera_angle": ["dynamic angle", "bird's eye", "worm's eye", "dutch angle"],
            },
            "futbol": {
                "visual_prompts": [
                    "epic football stadium atmosphere, crowd energy, dramatic lighting, sports cinematography",
                    "football player in action, dynamic motion capture, stadium lighting, athletic composition",
                    "football goal celebration, triumphant moment, confetti and atmosphere, emotional impact",
                    "tactical football analysis, strategic board, analytical composition, professional aesthetic",
                    "historic football moment, legendary player, archival quality, nostalgic atmosphere",
                ],
                "color_palette": ["#32CD32", "#FFFFFF", "#228B22", "#FFD700", "#000080"],
                "composition": ["action shot", "wide stadium", "close-up celebration", "tactical view"],
                "mood": ["energetic", "triumphant", "passionate", "dramatic"],
                "camera_angle": ["action tracking", "wide stadium", "celebration close-up", "tactical overhead"],
            },
            "duygusal": {
                "visual_prompts": [
                    "emotional human moment, authentic expression, soft natural lighting, intimate composition",
                    "heartwarming scene, warm golden hour, tender atmosphere, sentimental mood",
                    "dramatic emotional revelation, cinematic lighting, powerful composition, storytelling focus",
                    "nostalgic memory scene, dreamlike atmosphere, soft focus, emotional resonance",
                    "connection between people, intimate portrait, natural lighting, authentic emotion",
                ],
                "color_palette": ["#FF69B4", "#4169E1", "#FFB6C1", "#E6E6FA", "#DDA0DD"],
                "composition": ["intimate close-up", "environmental portrait", "soft focus", "depth of field"],
                "mood": ["emotional", "tender", "nostalgic", "dramatic"],
                "camera_angle": ["eye level", "close-up", "over shoulder", "soft focus"],
            },
            "motivasyon": {
                "visual_prompts": [
                    "inspiring success moment, triumphant pose, golden hour lighting, epic composition",
                    "athlete training scene, determination and effort, dramatic lighting, motivational atmosphere",
                    "mountain peak achievement, epic landscape, golden light, inspirational composition",
                    "entrepreneur or innovator at work, modern office, dynamic lighting, success aesthetic",
                    "overcoming obstacle scene, dramatic lighting, powerful composition, triumphant mood",
                ],
                "color_palette": ["#FFD700", "#FF8C00", "#FFA500", "#FF6347", "#DC143C"],
                "composition": ["epic wide shot", "triumphant pose", "dynamic action", "powerful center"],
                "mood": ["inspirational", "triumphant", "determined", "powerful"],
                "camera_angle": ["low angle", "epic wide", "dynamic tracking", "heroic perspective"],
            },
            "dramatik": {
                "visual_prompts": [
                    "intense dramatic scene, high contrast lighting, cinematic composition, powerful atmosphere",
                    "confrontation or conflict moment, dramatic angles, tense atmosphere, cinematic quality",
                    "suspenseful scene, mysterious lighting, shadow and contrast, thriller aesthetic",
                    "emotional climax, powerful performance, dramatic lighting, intense composition",
                    "plot twist revelation, dramatic reveal, cinematic lighting, shocking moment",
                ],
                "color_palette": ["#DC143C", "#8B0000", "#4B0082", "#2F4F4F", "#1C1C1C"],
                "composition": ["dramatic angle", "high contrast", "tension-filled", "powerful center"],
                "mood": ["intense", "suspenseful", "dramatic", "powerful"],
                "camera_angle": ["dutch angle", "low angle", "dramatic perspective", "extreme close-up"],
            },
        }

    def get_enhanced_visual_prompt(
        self,
        base_prompt: str,
        content_type: str,
        scene_index: int = 1
    ) -> str:
        """
        Base prompt'u içerik tipine göre zenginleştirir.

        Args:
            base_prompt: Orijinal prompt
            content_type: İçerik tipi
            scene_index: Sahne indeksi (varyasyon için)

        Returns:
            Zenginleştirilmiş görsel prompt
        """
        template = self.templates.get(content_type, self.templates["komik"])

        # Varyasyon için rastgele seçim
        visual_prompt = random.choice(template["visual_prompts"])
        color = random.choice(template["color_palette"])
        composition = template["composition"][scene_index % len(template["composition"])]
        mood = random.choice(template["mood"])
        camera_angle = template["camera_angle"][scene_index % len(template["camera_angle"])]

        # Prompt'u birleştir
        enhanced_prompt = (
            f"{base_prompt}. "
            f"{visual_prompt}. "
            f"Color palette with {color} accents. "
            f"Composition: {composition}. "
            f"Mood: {mood}. "
            f"Camera angle: {camera_angle}. "
            f"Cinematic lighting, photorealistic, 4K quality, vertical 9:16 format."
        )

        return enhanced_prompt

    def get_scene_specific_elements(
        self,
        content_type: str,
        scene_index: int = 1
    ) -> Dict[str, str]:
        """
        Sahne için özel görsel öğeler döndürür.

        Args:
            content_type: İçerik tipi
            scene_index: Sahne indeksi

        Returns:
            Görsel öğeler dict (emoji, overlay_text, frame_style)
        """
        template = self.templates.get(content_type, self.templates["komik"])

        elements = {
            "emoji": self._get_emoji_for_type(content_type),
            "overlay_text": self._get_overlay_text(content_type, scene_index),
            "frame_style": template["composition"][scene_index % len(template["composition"])],
            "color_accent": random.choice(template["color_palette"]),
        }

        return elements

    def _get_emoji_for_type(self, content_type: str) -> str:
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

    def _get_overlay_text(self, content_type: str, scene_index: int) -> str:
        """İçerik tipine göre overlay metni döndürür."""
        overlay_texts = {
            "komik": ["BEKLENMEDİK!", "İNANILMAZ!", "KAÇIRMAYIN!", "VİRAL OLACAK!"],
            "kedi": ["ÇOK SEVİMLİ!", "TATLI BİR AN!", "KEDİ DÜNYASI!", "MİYAV!"],
            "tarih": ["BUNU BİLİYOR MUYDUN?", "TARİHİ GERÇEK!", "GEÇMİŞTEN GÜNÜMÜZE!", "SIRRLAR ORTAYA ÇIKIYOR!"],
            "viral": ["TREND!", "GÜNCEL KONU!", "HERKES KONUŞUYOR!", "VİRAL OLACAK!"],
            "futbol": ["GOL!", "ŞAMPİYON!", "EFSANE!", "TARİHİ AN!"],
            "duygusal": ["DOKUNUCU!", "GERÇEK HİKAYE!", "KALBİNİ ETKİLEYECEK!", "EMPATİ!"],
            "motivasyon": ["BAŞARI!", "HAYATINI DEĞİŞTİR!", "GÜÇLÜ OL!", "İLHAM VERİCİ!"],
            "dramatik": ["ŞOK EDİCİ!", "GERİLİM!", "BEKLENMEDİK!", "DRAMATİK AN!"],
        }

        texts = overlay_texts.get(content_type, overlay_texts["komik"])
        return texts[scene_index % len(texts)]


def enhance_scene_visuals(
    scenes: List[dict],
    content_type: str = "komik"
) -> List[dict]:
    """
    Sahne görsel prompt'larını içerik tipine göre zenginleştirir.

    Args:
        scenes: Sahne listesi
        content_type: İçerik tipi

    Returns:
        Zenginleştirilmiş sahne listesi
    """
    template_manager = VisualTemplateManager()

    for scene in scenes:
        scene_index = scene.get("index", 1)
        base_prompt = scene.get("visual_prompt", "")

        # Görsel prompt'u zenginleştir
        enhanced_prompt = template_manager.get_enhanced_visual_prompt(
            base_prompt, content_type, scene_index
        )
        scene["visual_prompt"] = enhanced_prompt

        # Özel görsel öğeleri ekle
        visual_elements = template_manager.get_scene_specific_elements(content_type, scene_index)
        scene["visual_elements"] = visual_elements

    logger.info(f"✓ {len(scenes)} sahne görseli {content_type} tipine göre zenginleştirildi")
    return scenes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test
    test_scenes = [
        {"index": 1, "visual_prompt": "A funny situation", "duration_seconds": 5},
        {"index": 2, "visual_prompt": "Another moment", "duration_seconds": 5},
    ]

    enhanced = enhance_scene_visuals(test_scenes, "komik")

    for scene in enhanced:
        print(f"Sahne {scene['index']}: {scene['visual_prompt'][:100]}...")
        print(f"Öğeler: {scene['visual_elements']}")