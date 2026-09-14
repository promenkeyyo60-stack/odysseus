"""
topic_finder.py — Günlük trending konuları NewsAPI + GPT-4o ile bulur.
Her video tipi için ayrı, viral potansiyelli bir konu seçer.
"""

import logging
import random
from datetime import datetime
from typing import Optional

import httpx
from openai import OpenAI

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


#
# NewsAPI — Güncel haberler
#

def fetch_trending_news(category: str = "general", count: int = 10) -> list[dict]:
    """NewsAPI'den trending haberler çeker. Çalışmazsa fallback konular döndürür."""
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": cfg.NEWS_API_KEY,
            "country": cfg.NEWS_COUNTRY,
            "category": category,
            "pageSize": count,
            "language": cfg.NEWS_LANGUAGE,
        }
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        articles = data.get("articles", [])
        results = []
        for a in articles:
            if not a.get("title") or a["title"] == "[Removed]":
                continue
            results.append({
                "title":       a.get("title", ""),
                "description": a.get("description", ""),
                "source":      a.get("source", {}).get("name", ""),
                "url":         a.get("url", ""),
                "published":   a.get("publishedAt", ""),
            })
        logger.info(f"NewsAPI: {len(results)} haber çekildi [{category}]")
        return results

    except Exception as e:
        logger.warning(f"NewsAPI hatası: {e} - Fallback konular kullanılıyor")
        return _get_fallback_topics(category, count)

def _get_fallback_topics(category: str = "general", count: int = 10) -> list[dict]:
    """NewsAPI çalışmazsa alternatif konular döndürür."""
    fallback_topics = {
        "general": [
            {"title": "Günlük yaşamın ilginç yönleri", "description": "Her gün yeni keşfedeceğiniz şeyler"},
            {"title": "Teknoloji dünyasındaki son gelişmeler", "description": "Yenilikler ve trendler"},
            {"title": "Sağlıklı yaşam ipuçları", "description": "Günlük rutininizi geliştirin"},
            {"title": "Motivasyon ve kişisel gelişim", "description": "Hedeflerinize ulaşın"},
            {"title": "Eğlenceli bilgi ve genel kültür", "description": "Öğrenmeye değer gerçekler"},
        ],
        "entertainment": [
            {"title": "Viral sosyal medya trendleri", "description": "Herkesin konuştuğu konular"},
            {"title": "Eğlence dünyasından son gelişmeler", "description": "Film, müzik ve daha fazlası"},
            {"title": "Komik ilginç anlar", "description": "Gülmekten yere yıkılacaklar"},
            {"title": "Popüler kültür analizleri", "description": "Trendlerin arkasındaki hikayeler"},
        ],
        "technology": [
            {"title": "Yapay zeka dünyasındaki son gelişmeler", "description": "AI devrimi devam ediyor"},
            {"title": "Mobil teknoloji trendleri", "description": "Akıllı telefon ve uygulamalar"},
            {"title": "İnternet güvenliği ipuçları", "description": "Dijital güvenliğinizi koruyun"},
            {"title": "Bilimsel keşifler ve yenilikler", "description": "Teknoloji dünyasından haberler"},
        ],
        "science": [
            {"title": "Uzay ve astronomi keşifleri", "description": "Evrenin gizemleri"},
            {"title": "Çevre ve doğa koruma", "description": "Sürdürülebilir yaşam"},
            {"title": "Tıbbi bilimlerdeki yenilikler", "description": "Sağlık alanında gelişmeler"},
            {"title": "Fizik ve kimya ilginçlikleri", "description": "Bilimin eğlenceli tarafı"},
        ],
    }

    topics = fallback_topics.get(category, fallback_topics["general"])
    results = []
    for i, topic in enumerate(topics[:count]):
        results.append({
            "title": topic["title"],
            "description": topic["description"],
            "source": "Internal Topic Generator",
            "url": "",
            "published": datetime.now().isoformat(),
        })

    logger.info(f"Fallback: {len(results)} alternatif konu oluşturuldu [{category}]")
    return results


def fetch_all_news() -> list[dict]:
    """Tüm kategorilerden haber çeker, karıştırır."""
    all_news = []
    for cat in cfg.NEWS_CATEGORIES:
        articles = fetch_trending_news(category=cat, count=cfg.NEWS_MAX_ARTICLES // len(cfg.NEWS_CATEGORIES))
        all_news.extend(articles)

    # Karıştır — aynı kategorinin başta gelmesini engelle
    random.shuffle(all_news)
    return all_news[:cfg.NEWS_MAX_ARTICLES]


# 
# GPT-4o — Viral konu seçici
# 

def select_viral_topic(
    content_config: dict,
    news_articles: list[dict],
    used_topics: list[str] | None = None,
) -> dict:
    """
    GPT-4o ile verilen içerik tipine uygun viral bir konu seçer.

    Args:
        content_config: CONTENT_SCHEDULE'deki bir eleman (type, prompt_hint, ...)
        news_articles:  NewsAPI'den gelen haberler
        used_topics:    Bu gün zaten kullanılan konular (tekrar önlemek için)

    Returns:
        {
            "topic": str,           # Seçilen konu başlığı
            "angle": str,           # İşlenme açısı
            "hook": str,            # İlk 3 saniye cümlesi (dikkat çekici)
            "keywords": list[str],  # YouTube SEO anahtar kelimeleri
            "source_headline": str, # Kaynak haber başlığı (varsa)
            "rationale": str,       # Neden viral olabilir
        }
    """
    from pipeline.llm_client import call_llm_json

    # Haber özetini oluştur
    news_context = ""
    if news_articles:
        headlines = [f"- {a['title']}" for a in news_articles[:15] if a.get("title")]
        news_context = "Bugünkü trending haberler:\n" + "\n".join(headlines)

    # Kullanılmış konuları hariç tut
    used_context = ""
    if used_topics:
        used_context = f"\nBugün zaten kullanılan konular (BUNLARI KULLANMA):\n" + "\n".join(f"- {t}" for t in used_topics)

    system_prompt = f"""Sen bir YouTube Shorts içerik uzmanısın. Viral potansiyelli, {cfg.LANGUAGE} dilinde, 
{cfg.CHANNEL_THEME} tarzında Shorts videoları için konu seçiyorsun.

İçerik tipi: {content_config['type']} — {content_config['prompt_hint']}
Hook stili: {content_config['hook_style']}

Seçeceğin konu:
- 45-60 saniyede anlatılabilmeli
- İzleyiciyi ilk 3 saniyede yakalamalı
- Duygusal tepki uyandırmalı (güldür, dokunsun, şok et veya ilham ver)
- Türkiye veya dünya gündeminden ilham alabilir ama özgün olmalı
- Başlık merak uyandırıcı olmalı (clickbait değil, gerçek merak)

Yanıt olarak SADECE şu JSON formatını döndür, başka bir şey yazma:
{{
  "topic": "Konunun kısa başlığı",
  "angle": "Videoyu nasıl işleyeceğiz (yaklaşım açısı)",
  "hook": "İlk 3 saniyede söylenecek dikkat çekici cümle",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "source_headline": "Eğer bir haberden esinlendiysen o haber başlığı, yoksa boş bırak",
  "rationale": "Neden viral olabilir (1 cümle)"
}}"""

    user_msg = f"{news_context}\n{used_context}\n\nYukarıdaki kısıtları göz önünde bulundurarak en iyi konuyu seç."

    result = call_llm_json(system_prompt, user_msg, temperature=0.9, max_tokens=2000)
    if result and "topic" in result:
        logger.info(f"Konu seçildi: {result.get('topic', '?')} [{content_config['type']}]")
        return result

    # Fallback konu
    logger.info("Konu seciminde fallback kullaniliyor")
    return {
        "topic": f"{content_config['label']} — Bugünün Konusu",
        "angle": content_config["prompt_hint"],
        "hook": "Bunu duymak için son şansın...",
        "keywords": ["viral", "shorts", content_config["type"], "trending", "2025"],
        "source_headline": "",
        "rationale": "Genel viral format",
    }


# 
# Ana fonksiyon
# 

def find_daily_topics() -> list[dict]:
    """
    Günlük video planı için tüm konuları bulur.

    Returns:
        Her video için topic bilgisi içeren liste.
        cfg.CONTENT_SCHEDULE ile aynı sırada.
    """
    logger.info(" Günlük konular aranıyor...")
    news = fetch_all_news()

    topics = []
    used = []

    for content_cfg in cfg.CONTENT_SCHEDULE:
        topic = select_viral_topic(
            content_config=content_cfg,
            news_articles=news,
            used_topics=used,
        )
        topic["content_config"] = content_cfg  # Birleştir
        topic["label"] = content_cfg["label"]
        topics.append(topic)
        used.append(topic.get("topic", ""))

    logger.info(f" {len(topics)} konu hazır")
    return topics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    topics = find_daily_topics()
    for i, t in enumerate(topics, 1):
        print(f"\n{'='*50}")
        print(f"Video {i}: {t['label']}")
        print(f"Konu: {t['topic']}")
        print(f"Hook: {t['hook']}")
        print(f"Açı: {t['angle']}")
        print(f"Keywords: {', '.join(t.get('keywords', []))}")
