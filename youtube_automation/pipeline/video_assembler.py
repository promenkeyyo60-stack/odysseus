"""
video_assembler.py — FFmpeg ile YouTube Shorts montaj modulu.
Ken Burns zoom/pan efekti, gelismis altyazi stili, sahne gecis animasyonlari.
"""

import logging
import math
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)

JSON2VIDEO_BASE = cfg.JSON2VIDEO_BASE_URL


# ══════════════════════════════════════════════════
# Altyazi Yardimcilari
# ══════════════════════════════════════════════════

def _format_srt_time(seconds: float) -> str:
    """Saniyeyi SRT zaman damgasi formatina donusturur (00:00:00,000)."""
    millis = int((seconds - int(seconds)) * 1000)
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_subtitles(scenes: list) -> list:
    """
    Sahne listesinden SRT altyazi zamanlama listesi olusturur.
    Her sahneyi 2-3 satirda gosterir (okunabilirlik icin).
    """
    subtitles = []
    current_time = 0.0

    for scene in scenes:
        dur   = float(scene.get("duration_seconds", 5))
        chunk = scene.get("narration_chunk", "").strip()
        if not chunk:
            current_time += dur
            continue

        # Uzun metni kelimelere bol, en fazla 7 kelimelik satirlar
        words = chunk.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(current_line) >= 7:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))

        # Her satiri es sure dilimlere bol
        if lines:
            line_dur = dur / len(lines)
            for i, line in enumerate(lines):
                start = current_time + i * line_dur
                end   = start + line_dur - 0.1
                subtitles.append({
                    "start": round(start, 3),
                    "end":   round(end, 3),
                    "text":  line,
                })

        current_time += dur

    return subtitles


# ══════════════════════════════════════════════════
# Ken Burns Efekti — Zoom + Pan
# ══════════════════════════════════════════════════

def _build_ken_burns_filter(duration: float, scene_index: int, asset_type: str) -> str:
    """
    FFmpeg zoompan filtresi ile Ken Burns efekti uretir.
    Her sahne icin farkli yon (cevresinde donuyor) kullanir.
    Sadece statik gorseller icin uygulanir.
    """
    if asset_type == "video":
        # Video klipte zoom gerekmez, sadece scale+crop
        return "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280"

    zoom_factor = getattr(cfg, "KEN_BURNS_ZOOM_FACTOR", 1.08)
    fps = cfg.VIDEO_FPS
    total_frames = int(duration * fps)

    # Her sahne icin farkli zoom yonu (4 dongusel secenek)
    direction = scene_index % 4
    if direction == 0:
        # Zoom in — merkeze
        vf = (
            f"scale=8000:-1,"
            f"zoompan=z='min(zoom+0.0008,{zoom_factor})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:s=720x1280:fps={fps}"
        )
    elif direction == 1:
        # Zoom in — sol ust
        vf = (
            f"scale=8000:-1,"
            f"zoompan=z='min(zoom+0.0008,{zoom_factor})':x='0':y='0'"
            f":d={total_frames}:s=720x1280:fps={fps}"
        )
    elif direction == 2:
        # Zoom in — sag alt
        vf = (
            f"scale=8000:-1,"
            f"zoompan=z='min(zoom+0.0008,{zoom_factor})':x='iw/zoom*0.1':y='ih/zoom*0.1'"
            f":d={total_frames}:s=720x1280:fps={fps}"
        )
    else:
        # Pan soldan saga
        vf = (
            f"scale=8000:-1,"
            f"zoompan=z='1.04':x='if(lte(on,1),0,x+1)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:s=720x1280:fps={fps}"
        )

    return vf


# ══════════════════════════════════════════════════
# FFmpeg — Ana Montaj
# ══════════════════════════════════════════════════

def assemble_video_ffmpeg(
    script: dict,
    scene_assets: list,
    audio_path: Optional[Path],
    output_path: Path,
    subtitles: list,
) -> Optional[Path]:
    """
    FFmpeg ile 9:16 dikey Shorts videosu montajlar.
    - Ken Burns zoom/pan efekti (statik gorseller icin)
    - Gelismis altyazi stili
    - Ses senkronizasyonu
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_path.parent / f"ffmpeg_tmp_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        scenes    = script.get("scenes", [])
        asset_map = {a["index"]: a for a in scene_assets if a.get("file")}

        # 1. SRT altyazi dosyasi olustur
        srt_path  = temp_dir / "subtitles.srt"
        srt_lines = []
        for i, sub in enumerate(subtitles, 1):
            srt_lines.append(
                f"{i}\n{_format_srt_time(sub['start'])} --> {_format_srt_time(sub['end'])}\n{sub['text']}\n"
            )
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

        # 2. Her sahne icin klip olustur (Ken Burns dahil)
        scene_clips = []
        for scene in scenes:
            idx   = scene.get("index", 1)
            dur   = max(float(scene.get("duration_seconds", 5)), 2.0)
            asset = asset_map.get(idx)

            if not asset or not asset.get("file") or not Path(asset["file"]).exists():
                logger.warning(f"Sahne {idx} icin gorsel bulunamadi, atlaniyor")
                continue

            src_file   = Path(asset["file"])
            clip_path  = temp_dir / f"clip_{idx:02d}.mp4"
            asset_type = asset.get("type", "image")

            if asset_type == "video":
                # Video klip: kes ve dikey boyuta olcekle
                cmd = [
                    "ffmpeg", "-y", "-i", str(src_file),
                    "-t", str(dur),
                    "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
                    "-r", str(cfg.VIDEO_FPS),
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-an", str(clip_path),
                ]
            else:
                # Statik gorsel: Ken Burns efektiyle video yap
                ken_burns_enabled = getattr(cfg, "KEN_BURNS_ENABLED", True)
                if ken_burns_enabled:
                    vf = _build_ken_burns_filter(dur, idx, asset_type)
                else:
                    vf = "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280"

                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", str(src_file),
                    "-t", str(dur),
                    "-vf", vf,
                    "-r", str(cfg.VIDEO_FPS),
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-tune", "stillimage", "-pix_fmt", "yuv420p",
                    "-an", str(clip_path),
                ]

            result = subprocess.run(cmd, capture_output=True, timeout=120)
            if result.returncode != 0:
                logger.warning(
                    f"Sahne {idx} klip hatasi, basit olcekle deneniyor: "
                    f"{result.stderr[-200:].decode('utf-8', errors='ignore')}"
                )
                # Hata durumunda basit olcekleme ile tekrar dene
                cmd_simple = [
                    "ffmpeg", "-y", "-loop", "1", "-i", str(src_file),
                    "-t", str(dur),
                    "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
                    "-r", str(cfg.VIDEO_FPS),
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-an", str(clip_path),
                ]
                subprocess.run(cmd_simple, capture_output=True, check=True, timeout=120)

            if clip_path.exists() and clip_path.stat().st_size > 0:
                scene_clips.append(clip_path)

        if not scene_clips:
            logger.error("Montaj icin hicbir sahne klibi olusturulamadi!")
            return None

        # 3. Klipleri birlestir (concat demuxer)
        concat_list = temp_dir / "concat.txt"
        concat_content = "\n".join(
            f"file '{str(c.resolve()).replace(chr(92), '/')}'" for c in scene_clips
        )
        concat_list.write_text(concat_content, encoding="utf-8")

        merged_video = temp_dir / "merged_no_audio.mp4"
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(merged_video),
        ]
        subprocess.run(cmd_concat, capture_output=True, check=True, timeout=120)

        # 4. Altyazi stil ayarlari (config'den)
        font_size  = getattr(cfg, "SUBTITLE_FONT_SIZE", 24)
        font_name  = getattr(cfg, "SUBTITLE_FONT_NAME", "Arial")
        bold       = 1 if getattr(cfg, "SUBTITLE_BOLD", True) else 0
        outline    = getattr(cfg, "SUBTITLE_OUTLINE", 2.5)
        margin_v   = getattr(cfg, "SUBTITLE_MARGIN_V", 130)

        srt_escaped = str(srt_path.resolve()).replace("\\", "/").replace(":", "\\:")
        sub_filter = (
            f"subtitles='{srt_escaped}':"
            f"force_style='FontSize={font_size},FontName={font_name},Bold={bold},"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"BorderStyle=1,Outline={outline},Alignment=2,MarginV={margin_v}'"
        )

        # 5. Final render: ses + altyazi
        final_cmd = ["ffmpeg", "-y", "-i", str(merged_video)]

        if audio_path and Path(audio_path).exists():
            final_cmd.extend(["-i", str(audio_path)])
            final_cmd.extend([
                "-vf", sub_filter,
                "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_path),
            ])
        else:
            final_cmd.extend([
                "-vf", sub_filter,
                "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
                str(output_path),
            ])

        res = subprocess.run(final_cmd, capture_output=True, text=True, timeout=300)
        if res.returncode != 0:
            logger.error(f"FFmpeg final montaj hatasi: {res.stderr[-500:]}")
            return None

        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(
            f"  FFmpeg ile video basariyla olusturuldu: "
            f"{output_path.name} ({size_mb:.1f} MB)"
        )
        return output_path

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg islem suresi asimi!")
        return None
    except Exception as e:
        logger.error(f"FFmpeg montaj hatasi: {e}")
        return None
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


# ══════════════════════════════════════════════════
# JSON2Video API (isteğe bagli yedek)
# ══════════════════════════════════════════════════

def build_movie_payload(
    scenes: list,
    scene_assets: list,
    audio_path: Optional[Path],
    subtitles: list,
    title: str = "",
) -> dict:
    """JSON2Video API icin payload olusturur."""
    asset_map = {a["index"]: a for a in scene_assets if a.get("file")}
    elements  = []

    for scene in scenes:
        idx   = scene.get("index", 1)
        dur   = scene.get("duration_seconds", 5)
        asset = asset_map.get(idx)

        if not asset or not asset.get("file"):
            continue

        file_path = Path(asset["file"])
        if not file_path.exists():
            continue

        elem_type = "video" if asset.get("type") == "video" else "image"
        elements.append({
            "type":     elem_type,
            "src":      str(file_path),
            "duration": dur,
            "settings": {"volume": 0},
        })

    # Seslendirme ekle
    if audio_path and Path(audio_path).exists():
        elements.append({
            "type": "audio",
            "src":  str(audio_path),
            "settings": {"volume": 1},
        })

    return {
        "resolution": "custom",
        "width":      cfg.VIDEO_WIDTH,
        "height":     cfg.VIDEO_HEIGHT,
        "fps":        cfg.VIDEO_FPS,
        "scenes":     [{"elements": elements}],
    }


def submit_movie(payload: dict) -> Optional[str]:
    """JSON2Video'ya istek gonder, movie ID dondurur."""
    if not cfg.JSON2VIDEO_API_KEY:
        return None
    try:
        headers = {"x-api-key": cfg.JSON2VIDEO_API_KEY, "Content-Type": "application/json"}
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{JSON2VIDEO_BASE}/movies", headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json().get("movie", {}).get("id")
    except Exception as e:
        logger.error(f"JSON2Video istek hatasi: {e}")
        return None


def poll_movie(movie_id: str, max_wait: int = 300, poll_interval: int = 10) -> Optional[str]:
    """JSON2Video islemi tamamlanana kadar bekler."""
    if not cfg.JSON2VIDEO_API_KEY:
        return None
    headers = {"x-api-key": cfg.JSON2VIDEO_API_KEY}
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(f"{JSON2VIDEO_BASE}/movies/{movie_id}", headers=headers)
                resp.raise_for_status()
                data  = resp.json()
                movie = data.get("movie", {})
            status = movie.get("status", "")
            logger.info(f"  JSON2Video: {status} — {elapsed}sn")
            if status == "done":
                return movie.get("url")
            elif status == "failed":
                logger.error(f"JSON2Video basarisiz: {movie.get('message', '')}")
                return None
        except Exception as e:
            logger.warning(f"JSON2Video polling hatasi: {e}")
    logger.error(f"JSON2Video timeout ({max_wait}sn)")
    return None


def download_final_video(url: str, output_path: Path) -> Optional[Path]:
    """Final videoyu indirir."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        logger.info(f"  Final video indiriliyor...")
        with httpx.Client(timeout=180, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"  Final video kaydedildi: {output_path.name} ({size_mb:.1f} MB)")
        return output_path
    except Exception as e:
        logger.error(f"Video indirme hatasi: {e}")
        return None


# ══════════════════════════════════════════════════
# Ana Orchestrator
# ══════════════════════════════════════════════════

def assemble_video(
    script: dict,
    scene_assets: list,
    audio_path: Optional[Path],
    output_path: Path,
    content_type: str = "komik",
) -> Optional[Path]:
    """
    Tum parcalari birlestirip final Shorts videosu uretir.
    Oncelik: MoviePy (profesyonel) -> FFmpeg (yerel) -> JSON2Video API

    Args:
        script: Senaryo verisi
        scene_assets: Sahne gorsel/video listesi
        audio_path: Ses dosyasi yolu
        output_path: Cikti video yolu
        content_type: Icerik tipi (altyazi stilleri icin)
    """
    scenes = script.get("scenes", [])
    title  = script.get("title", "")

    if not scenes:
        logger.error("Sahne bulunamadi!")
        return None

    # Altyazi olustur
    subtitles = generate_subtitles(scenes)
    logger.info(f"  {len(subtitles)} altyazi satiri olusturuldu")

    # 1. MoviePy ile profesyonel montaj (öncelik)
    try:
        # Check if MoviePy assembler module can be imported
        from moviepy_assembler import assemble_video_moviepy, MOVIEPY_AVAILABLE
        if MOVIEPY_AVAILABLE:
            logger.info("  MoviePy ile profesyonel montaj baslatiliyor...")
            res = assemble_video_moviepy(script, scene_assets, audio_path, output_path, content_type)
            if res:
                return res
            logger.warning("MoviePy montaji basarisiz, FFmpeg deneniyor...")
        else:
            logger.info("  MoviePy kurulmemis, FFmpeg kullaniliyor...")
    except ImportError as e:
        logger.info(f"  MoviePy assembler kurulmemis: {e}, FFmpeg kullaniliyor...")
    except Exception as e:
        logger.warning(f"MoviePy hatasi: {e}, FFmpeg deneniyor...")

    # 2. Yerel FFmpeg montaj (fallback)
    if getattr(cfg, "USE_LOCAL_FFMPEG", True):
        logger.info("  FFmpeg ile yerel montaj baslatiliyor...")
        res = assemble_video_ffmpeg(script, scene_assets, audio_path, output_path, subtitles)
        if res:
            return res
        logger.warning("FFmpeg montaji basarisiz, JSON2Video deneniyor...")

    # 3. JSON2Video API (son fallback)
    if cfg.JSON2VIDEO_API_KEY:
        payload  = build_movie_payload(scenes, scene_assets, audio_path, subtitles, title)
        movie_id = submit_movie(payload)
        if movie_id:
            video_url = poll_movie(movie_id)
            if video_url:
                return download_final_video(video_url, output_path)

    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("video_assembler.py — Test icin: python run.py --test")
