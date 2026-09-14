# -*- coding: utf-8 -*-
import feedparser
import anthropic # OpenAI yerine Anthropic kütüphanesini ekledik

# Claude API anahtarını buraya yazmalısın
# API anahtarını https://console.anthropic.com/ adresinden alabilirsin
client = anthropic.Anthropic(
    api_key="SENIN_CLAUDE_API_ANAHTARIN"
)

def fetch_viral_news():
    rss_url = "https://www.ntv.com.tr/gundem.rss"
    feed = feedparser.parse(rss_url)
    if feed.entries:
        top_article = feed.entries[0]
        return {
            "title": top_article.get("title"),
            "description": top_article.get("summary", top_article.get("title")),
            "url": top_article.get("link")
        }
    return None

def generate_shorts_script(news_data):
    prompt = f"""
    Asagidaki guncel haberi incele. Bunu YouTube Shorts icin 30-40 saniyelik,
    izleyiciyi ilk 3 saniyede yakalayacak guclu bir kanca iceren, tamamen ozgun,
    akici ve merak uyandirici bir video senaryosuna donustur. Telif hakki sorunu yaratmayacak
    sekilde kendi kelimelerinle yeniden kurgula. Sadece seslendirme metnini ver.

    Haber Basligi: {news_data['title']}
    Haber Detayi: {news_data['description']}
    """

    # Claude API çağrısı
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text

if __name__ == "__main__":
    print("Güncel haberler RSS üzerinden taranıyor...")
    news = fetch_viral_news()
    if news:
        print(f"\n[+] Seçilen Haber: {news['title']}\n")
        print("Claude yapay zeka senaryoyu yazıyor...")
        try:
            script = generate_shorts_script(news)
            print("\n--- OLUŞTURULAN YOUTUBE SHORTS SENARYOSU ---")
            print(script)
            print("-" * 50)
        except Exception as e:
            print(f"Bir hata oluştu: {e}")
    else:
        print("Haber çekilemedi.")
