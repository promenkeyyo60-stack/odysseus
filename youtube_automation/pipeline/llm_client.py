"""
llm_client.py — Ortak LLM istemcisi (Gemini & OpenAI)
Gemini 2.0 Flash ve OpenAI modellerini otomatik yonetir.
"""

import json
import logging
import re
from typing import Optional, Tuple
from pathlib import Path

from openai import OpenAI

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


def get_llm_client() -> Tuple[Optional[OpenAI], str]:
    """
    En iyi kullanilabilir LLM istemcisini ve model adini dondurur.
    Oncelik: Gemini -> OpenAI
    """
    if cfg.GEMINI_API_KEY:
        try:
            client = OpenAI(
                base_url=cfg.GEMINI_BASE_URL,
                api_key=cfg.GEMINI_API_KEY,
            )
            return client, cfg.GEMINI_MODEL
        except Exception as e:
            logger.warning(f"Gemini client olusturulamadi: {e}")

    if cfg.OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=cfg.OPENAI_API_KEY)
            return client, cfg.OPENAI_MODEL
        except Exception as e:
            logger.warning(f"OpenAI client olusturulamadi: {e}")

    return None, ""


def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.85,
    max_tokens: int = 3000,
) -> Optional[dict]:
    """
    LLM'e istek atip JSON yanitini parse eder.
    Gemini ve OpenAI arasinda otomatik fallback yapar.
    Rate limit durumunda exponential backoff uygular.
    """
    import time

    clients_to_try = []

    if cfg.GEMINI_API_KEY:
        clients_to_try.append((
            "Gemini",
            OpenAI(base_url=cfg.GEMINI_BASE_URL, api_key=cfg.GEMINI_API_KEY),
            cfg.GEMINI_MODEL,
        ))

    if cfg.OPENAI_API_KEY:
        clients_to_try.append((
            "OpenAI",
            OpenAI(api_key=cfg.OPENAI_API_KEY),
            cfg.OPENAI_MINI_MODEL,
        ))

    for name, client, model in clients_to_try:
        for attempt in range(3):
            try:
                logger.info(f"LLM istegi yapiliyor: {name} ({model})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    max_tokens=max(max_tokens, 4000),  # Senaryo icin yeterli alan
                )
                raw_text = response.choices[0].message.content or "{}"

                data = _parse_json_robust(raw_text, name)
                if data:
                    logger.info(f"LLM basarili: {name}")
                    return data

                logger.warning(f"{name} gecersiz JSON dondu, tekrar deneniyor...")
                continue

            except Exception as e:
                err_str = str(e).lower()
                # Bakiye/kota yok — bu client'i atla, beklemeden gec
                if "credit" in err_str or "billing" in err_str or "insufficient_quota" in err_str:
                    logger.warning(f"{name} bakiye yok, atlaniyor.")
                    break
                # Rate limit — bekle ve tekrar dene
                elif "429" in str(e) or "rate" in err_str or "quota" in err_str:
                    wait = 15 * (attempt + 1)
                    logger.warning(f"{name} rate limit, {wait}sn bekleniyor...")
                    time.sleep(wait)
                    continue
                # 503 — kisa bekleme
                elif "503" in str(e) or "unavailable" in err_str:
                    time.sleep(5)
                    continue
                else:
                    logger.warning(f"{name} ({model}) hatasi: {e}")
                    break  # Bu client icin denemeyi birak, sonrakine gec

    return None


def _parse_json_robust(raw_text: str, source: str = "") -> Optional[dict]:
    """
    JSON parse etmeye calisir. Basarisiz olursa kesik JSON'u onarir.
    Gemini bazen token limitinde JSON'u yarim birakir — bunu yakalarız.
    """
    # 1. Kod bloklarini temizle
    cleaned = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    # 2. JSON bloğunu bul
    match    = re.search(r"\{[\s\S]*\}", cleaned)
    json_str = match.group(0) if match else cleaned

    # 3. Kontrol karakterlerini temizle
    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', json_str)

    # 4. Direkt parse dene
    try:
        return json.loads(json_str, strict=False)
    except json.JSONDecodeError:
        pass

    # 5. Kesik JSON onarimi — acik kalan parantez/tırnakları kapat
    repaired = _repair_truncated_json(json_str)
    try:
        data = json.loads(repaired, strict=False)
        logger.info(f"  JSON onarildi ({source}): {len(repaired)} karakter")
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"  JSON onarilamadi ({source}): {e}")
        return None


def _repair_truncated_json(s: str) -> str:
    """
    Token limitinden kesilen JSON'u onarır.
    Açık kalan string tırnaklarını ve parantezleri kapatır.
    """
    # String içindeyse kapat
    in_string = False
    escape_next = False
    for ch in s:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string

    if in_string:
        s += '"'

    # Açık parantez sayısını dengele
    opens  = s.count('{') - s.count('}')
    arrays = s.count('[') - s.count(']')

    # Son yarım sahneyi/elemanı temizle: son virgülden önce kes
    if opens > 0 or arrays > 0:
        # Son geçerli virgülü bul ve orada kes
        last_valid = max(s.rfind('},'), s.rfind('"}'))
        if last_valid > len(s) // 2:
            s = s[:last_valid + 1]

    s += ']' * max(0, s.count('[') - s.count(']'))
    s += '}' * max(0, s.count('{') - s.count('}'))
    return s
