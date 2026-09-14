import sys
sys.path.insert(0, 'youtube_automation')
import config as cfg
import httpx

def check(name, key):
    if not key:
        print(f"  {name}: YOK")
        return False
    if len(key) < 20:
        print(f"  {name}: COK KISA ({len(key)} char) - muhtemelen gecersiz")
        return False
    print(f"  {name}: VAR ({len(key)} char)")
    return True

print("=== API KEY DURUMU ===")
check("Gemini    ", cfg.GEMINI_API_KEY)
check("OpenAI    ", cfg.OPENAI_API_KEY)
check("ElevenLabs", cfg.ELEVENLABS_API_KEY)
check("Runway    ", cfg.RUNWAY_API_KEY)
check("Luma      ", cfg.LUMA_API_KEY)
check("NewsAPI   ", cfg.NEWS_API_KEY)

print("\n=== CANLI API TESTLERI ===")

# ElevenLabs test
if cfg.ELEVENLABS_API_KEY and len(cfg.ELEVENLABS_API_KEY) > 20:
    try:
        r = httpx.get("https://api.elevenlabs.io/v1/user", headers={"xi-api-key": cfg.ELEVENLABS_API_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            sub = data.get("subscription", {})
            used = sub.get("character_count", 0)
            limit = sub.get("character_limit", 0)
            print(f"  ElevenLabs: CALISYOR - {used}/{limit} karakter kullanildi")
        else:
            print(f"  ElevenLabs: HATA {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"  ElevenLabs: BAGLANTI HATASI - {e}")

# Gemini test
if cfg.GEMINI_API_KEY and len(cfg.GEMINI_API_KEY) > 20:
    try:
        from openai import OpenAI
        client = OpenAI(base_url=cfg.GEMINI_BASE_URL, api_key=cfg.GEMINI_API_KEY)
        r = client.chat.completions.create(
            model=cfg.GEMINI_MODEL,
            messages=[{"role": "user", "content": "Say OK only."}],
            max_tokens=5,
        )
        print(f"  Gemini: CALISYOR - yanit: {r.choices[0].message.content}")
    except Exception as e:
        print(f"  Gemini: HATA - {e}")

# OpenAI test
if cfg.OPENAI_API_KEY and len(cfg.OPENAI_API_KEY) > 20:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=cfg.OPENAI_API_KEY)
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK only."}],
            max_tokens=5,
        )
        print(f"  OpenAI: CALISYOR - yanit: {r.choices[0].message.content}")
    except Exception as e:
        print(f"  OpenAI: HATA - {e}")

# Pollinations test
try:
    import urllib.request
    req = urllib.request.Request(
        "https://image.pollinations.ai/prompt/test?width=100&height=100&nologo=true",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        size = len(resp.read())
        print(f"  Pollinations: CALISYOR - {size} bytes gorsel")
except Exception as e:
    print(f"  Pollinations: HATA - {e}")

print("\nBitti.")
