"""
uploader.py — YouTube Data API v3 ile video yükleme ve dinamik SEO optimizasyonu.
Her video için çeşitlendirilmiş başlıklar ve SEO açıklamaları oluşturur.
"""

import logging
import random
from pathlib import Path
from typing import Optional, Dict, List
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config as cfg

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════
# Dinamik SEO Başlık Varyasyonları
# ══════════════════════════════════════════════════

TITLE_MODIFIERS = {
    "meditasyon": [
        "432Hz ile Derin Uyku",
        "Stres Giderme",
        "5 Dakikada Uykuya Dalın",
        "Derin Zihin Temizliği",
        "Rahatlama ve Huzur",
        "Gece Uyku Meditasyonu",
        "Anksiyete Karşı",
        "Tamamen Rahatla",
        "Yüksek Frekans",
        "Doğal Uyku İndüktörü"
    ],
    "motivasyon": [
        "Günde 1 Dakika",
        "Hayatını Değiştir",
        "Başarı Sırları",
        "Zihinsel Güç",
        "Kendine Güven",
        "Hedef Odaklı",
        "Pozitif Enerji",
        "Günlük Motivasyon",
        "Zirveye Giden Yol",
        "Sınırları Aş"
    ],
    "komik": [
        "İnanamayacaksınız",
        "Gülmekten Yere Yığılacaksınız",
        "Komik Anlar",
        "Viral Video",
        "Eğlence Garantili",
        "Kahkaha Bombası",
        "Gündem Oldu",
        "Trend Konu",
        "Sosyal Medya Fenomeni",
        "Komik Kısa Video"
    ],
    "tarih": [
        "Bunu Biliyor Muydunuz?",
        "Tarihin Gizemi",
        "Gerçekler Şok Edecek",
        "Bilinmeyen Yönler",
        "Tarihsel Gerçekler",
        "Geçmişin Sırları",
        "Tarih Öğreniyoruz",
        "Kültürel Miras",
        "Tarihi Anlar",
        "Efsaneler ve Gerçekler"
    ],
    "kedi": [
        "Kedi Severler İçin",
        "Sevimli Kediler",
        "Kedi Dünyası",
        "Komik Kedi Anları",
        "Evcil Hayvan Severler",
        "Kedi Sevgisi",
        "Patili Dostlar",
        "Kedi Sahipleri",
        "Tüyler Uçuşuyor",
        "Kedi Günlüğü"
    ],
    "futbol": [
        "Futbol Severler İçin",
        "Transfer Haberleri",
        "Futbol Gündemi",
        "Sahada Ol",
        "Futbol Tutkusu",
        "Maç Analizi",
        "Futbol İstatistikleri",
        "Derbi Heyecanı",
        "Futbol Dünyası",
        "Gol Makinesi"
    ],
    "viral": [
        "Trend Olan Konu",
        "Viral Video",
        "Gündem Yaratan",
        "Sosyal Medya Çılgınlığı",
        "Herkese Ulaşan",
        "Popüler Konu",
        "Trend Yakala",
        "Viral Etki",
        "Gündem Ol",
        "Sosyal Medya Fenomeni"
    ],
    "duygusal": [
        "Dokunucu Hikaye",
        "Göz Yaslatacak",
        "Kalbinizi Etkileyecek",
        "Duygusal Anlar",
        "İnsani Hikayeler",
        "Derin Duygular",
        "Gözyaşları",
        "Kalp Kırıklığı",
        "Duygusal Bağ",
        "İnsanlık Hali"
    ],
    "dramatik": [
        "Gerilim Dolu",
        "Şok Edici Gerçek",
        "İnanılmaz Hikaye",
        "Büyüleyici Anlatım",
        "Tansiyon Yüksek",
        "Mister Gerçekler",
        "Gerilim ve Aksiyon",
        "Sürükleyici Hikaye",
        "Heyecan Verici",
        "Akıl Almaz Durum"
    ],
    "genel": [
        "İlginç Bilgiler",
        "Gündem Konusu",
        "Bilmeye Değer",
        "Eğitici İçerik",
        "Bilgi Dolu",
        "Öğrenmeye Devam",
        "Genel Kültür",
        "Bilgi Paylaşımı",
        "Eğlenceli Bilgiler",
        "Keşfetmeye Değer"
    ]
}

# ══════════════════════════════════════════════════
# Dinamik SEO Hashtag'leri
# ══════════════════════════════════════════════════

SEO_HASHTAGS = {
    "meditasyon": [
        "#uykumeditasyonu", "#zihinmolası", "#stresgerdirme", "#derinuyku",
        "#rahatlatanmuzik", "#meditasyon", "#huzur", "#nedeniyorum",
        "#uykuilacı", "#gecemeditasyonu", "#432hz", "#thetafrekansı"
    ],
    "motivasyon": [
        "#motivasyon", "#başarı", "#gelişim", "#kendigelişimi",
        "#pozitifdüşünce", "#hedefler", "#günlükmotivasyon", "#özgüven",
        "#liderlik", "#başlangıcıyap", "#başarmak", "#ilham"
    ],
    "komik": [
        "#komik", "#eğlence", "#kahkaha", "#viral", "#gülmek",
        "#eğlenceli", "#shorts", "#trend", "#komikanlar", "#gülmece"
    ],
    "tarih": [
        "#tarih", "#bilgi", "#genelkültür", "#tarihselgerçekler",
        "#geçmiş", "#tarihinizmiraklı", "#bilinmeyenler", "#tarihbilimi",
        "#kültür", "#miras", "#tarihserseri"
    ],
    "kedi": [
        "#kedi", "#kedişi", "#kedisever", "#kedidünyası",
        "#evcilhayvan", "#patilidostlar", "#komikkedi", "#sevimlikedi",
        "#kedicom", "#kedi aşkı", "#pet", "#petlover"
    ],
    "futbol": [
        "#futbol", "#futbolsever", "#futbolgündemi", "#transfer",
        "#maç", "#derbi", "#sahol", "#gol", "#futboliçin",
        "#futbolanaliz", "#futbolistatistik", "#spor"
    ],
    "viral": [
        "#viral", "#trend", "#gündem", "#sosyalmedya",
        "#popüler", "#fenomen", "#trendyakala", "#shortsviral",
        "#keşfet", "#fyp", "#viralvideo", "#gündemol"
    ],
    "duygusal": [
        "#duygusal", "#hikaye", "#gözyaşı", "#kalp",
        "#insanlık", "#duygular", "#hissel", "#dokunucu",
        "#gerçekhikaye", "#anlamaya", "#duygusalbağ"
    ],
    "dramatik": [
        "#dramatik", "#gerilim", "#aksiyon", "#mister",
        "#şok", "#heyecan", "#gerilimdolu", "#sürükleyici",
        "#akılalmaz", "#büyüleyici", "#efsane"
    ],
    "genel": [
        "#bilgi", "#öğren", "#genelkültür", "#eğitici",
        "#ilginçbilgiler", "#bilgipaylaşımı", "#keşfet", "#faydalı",
        "#bilinmeyenler", "#haber", "#gündem"
    ]
}

# ══════════════════════════════════════════════════
# Dinamik Açıklama Şablonları
# ══════════════════════════════════════════════════

DESCRIPTION_TEMPLATES = {
    "meditasyon": [
        """Bu {title_modifier} meditasyonu ile derin rahatlama yaşayın. Stres ve gerginlikten uzaklaşın, zihninizi temizleyin ve huzurlu bir uykuya dalın. {hashtags}

Bu meditasyon pratiği:
• Stresi azaltmaya yardımcı olur
• Uyku kalitesini artırır
• Zihinsel berraklığı sağlar
• Negatif düşünceleri temizler

En iyi deneyim için kulaklık kullanın ve rahat bir pozisyonda oturun. {call_to_action}""",
        """{title_modifier} ile zihinsel dinlenme ve bedensel rahatlama deneyimi. Bu özel frekanslı meditasyon, gündelik stresinizi atmanıza ve derin uyku yakalamanıza yardımcı olur. {hashtags}

Bu videoda:
• Doğal uyku indüksiyonu teknikleri
• Stres yönetimi metodları
• Zihin temizleme egzersizleri
• Rahatlama rehberi

Her gün düzenli kullanarak farkı hissedin. {call_to_action}"""
    ],
    "motivasyon": [
        """{title_modifier} ile hayatınızı değiştirecek motivasyon dolu anlar. Bu video, sınırlarınızı aşmanıza ve hedeflerinize ulaşmanıza ilham verecek. {hashtags}

Videoda bulacağınız içerikler:
• Günlük motivasyon teknikleri
• Başarıya giden yol haritası
• Kendine güven inşa etme
• Pozitif düşünce egzersizleri

Her sabah izleyerek gününüza güçlü başlayın. {call_to_action}""",
        """{title_modifier} - Zihinsel gücünüzü keşfedin ve potansiyelinizi açığa çıkarın. Bu motivasyon videosu, hedeflerinize odaklanmanıza ve engelleri aşmanıza yardımcı olacak. {hashtags}

İçerik özeti:
• Hedef belirleme stratejileri
• Engellerle başa çıkma yöntemleri
• Sürekli gelişim alışkanlıkları
• Liderlik ve özgüven ipuçları

Motivasyonunuzu yüksek tutmak için abone olun. {call_to_action}"""
    ],
    "komik": [
        """{title_modifier} - Gülmekten yere yığılacağınız komik anlar! Bu video, günün stresini atmanıza ve kahkaha ile dolmanıza yardımcı olacak. {hashtags}

Videoda:
• Viral komik anlar
• Gündem komik durumlar
• Eğlenceli kamera şakaları
• Sosyal medya kahkahaları

Gülmek her şeyin ilacıdır! {call_to_action}""",
        """{title_modifier} ile kahkaha garantili anlar yaşayın. Bu eğlenceli video, gününüzü renklendirecek ve yüzünüzde tebessüm oluşturacak. {hashtags}

İçerik:
• Komik sahneler
• Eğlenceli durumlar
• Viral video anları
• Sosyal medya komikliği

Kahkaha ile gününüzü güzelleştirin. {call_to_action}"""
    ],
    "tarih": [
        """{title_modifier} - Tarihin ilginç ve bilinmeyen yönlerini keşfedin. Bu video, geçmişten günümüze uzanan sırları ve gerçekleri anlatıyor. {hashtags}

Videoda öğrenecekleriniz:
• Tarihsel olaylar ve gerçekler
• Bilinmeyen tarih faktları
• Kültürel miras ve etkileri
• Tarihsel analizler

Tarih öğrenmek hiç bu kadar eğlenceli olmamıştı! {call_to_action}""",
        """{title_modifier} ile geçmişin derinliklerine dalın. Bu tarihsel anlatım, olayların arka planını ve gerçek yüzünü ortaya koyuyor. {hashtags}

İçerik:
• Tarihsel gizemler
• Gerçekler ve efsaneler
• Tarihöncesi dönemi
• Kültürel etkileşimler

Tarih meraklıları için ideal içerik. {call_to_action}"""
    ],
    "kedi": [
        """{title_modifier} - Kedi severler için sevimli ve komik anlar. Bu video, tüy dostlarımızın en eğlenceli ve tatlı anlarını sergiliyor. {hashtags}

Videoda:
• Komik kedi anları
• Sevimli kedi davranışları
• Evcil hayvan sevgisi
• Kedi eğitimi ipuçları

Kedi aşkı için abone olun! {call_to_action}""",
        """{title_modifier} ile kedi dünyasının en özel anlarını keşfedin. Bu video, patili dostlarımızın sevimli komikliklerini ve eğlenceli davranışlarını gösteriyor. {hashtags}

İçerik:
• Kedi komikliği
• Sevimli anlar
• Evcil hayvan bakımı
• Kedi karakterleri

Kedi sahipleri için mükemmel içerik. {call_to_action}"""
    ],
    "futbol": [
        """{title_modifier} - Futbol dünyasından en son gelişmeler ve analizler. Bu video, futbol severler için özel içerikler sunuyor. {hashtags}

Videoda:
• Futbol gündemi
• Transfer haberleri
• Maç analizleri
• Futbol istatistikleri

Futbol tutkusu için bizi takip edin! {call_to_action}""",
        """{title_modifier} ile sahada olun. Bu video, futbol dünyasından ilginç haberler ve analizler içeriyor. {hashtags}

İçerik:
• Futbol gelişmeleri
• Derbi analizleri
• Oyuncu performansları
• Taktiksel incelemeler

Futbol bilginizi artırmak için ideal. {call_to_action}"""
    ],
    "viral": [
        """{title_modifier} - Sosyal medyada trend olan konular ve viral içerikler. Bu video, gündemi yakalamanıza yardımcı olacak. {hashtags}

Videoda:
• Viral trendler
• Sosyal medya gündemi
• Popüler konular
• Trend analizi

Gündemi kaçırmayın! {call_to_action}""",
        """{title_modifier} ile viral olmanın sırlarını keşfedin. Bu video, sosyal medya trendlerini ve popüler içerikleri analiz ediyor. {hashtags}

İçerik:
• Trend yakalama teknikleri
• Viral içerik stratejileri
• Sosyal medya analizi
• Popülerlik ipuçları

Sosyal medya başarısı için izleyin. {call_to_action}"""
    ],
    "duygusal": [
        """{title_modifier} - Kalbinizi etkileyecek dokunucu hikayeler. Bu video, insanlık ve duygusal bağların gücünü gösteriyor. {hashtags}

Videoda:
• Gerçek hikayeler
• Duygusal anlar
• İnsani değerler
• Toplumsal farkındalık

Göz yaşlarınızı kontrol edemeyebilirsiniz. {call_to_action}""",
        """{title_modifier} ile derin duygusal deneyim yaşayın. Bu video, insanlık hikayelerini ve duygusal bağları anlatıyor. {hashtags}

İçerik:
• Dokunucu hikayeler
• Duygusal derinlik
• İnsani değerler
• Empati kurma

Duygusal zeka için ideal içerik. {call_to_action}"""
    ],
    "dramatik": [
        """{title_modifier} - Gerilim dolu ve şok edici gerçekler. Bu video, büyüleyici hikayeler ve mister olaylar sunuyor. {hashtags}

Videoda:
• Gerilim dolu anlatım
• Şok edici gerçekler
• Mister olaylar
• Aksiyon dolu sahneler

Heyecan dolu dakikalar sizi bekliyor. {call_to_action}""",
        """{title_modifier} ile akıl almaz hikayeleri keşfedin. Bu video, dramatik anlatım ve sürükleyici içerikler sunuyor. {hashtags}

İçerik:
• Dramatik olaylar
• Gerilim ve aksiyon
• Mister gerçekler
• Büyüleyici hikayeler

Dramatik içerik severler için ideal. {call_to_action}"""
    ],
    "genel": [
        """{title_modifier} - İlginç bilgiler ve öğrenmeye değer içerikler. Bu video, genel kültürünüzü artıracak. {hashtags}

Videoda:
• İlginç bilgiler
• Genel kültür
• Eğitici içerik
• Bilgi paylaşımı

Öğrenmeye devam edin! {call_to_action}""",
        """{title_modifier} ile keşfetmeye değer bilgiler öğrenin. Bu video, genel kültür ve ilginç gerçekler sunuyor. {hashtags}

İçerik:
• Bilgi dolu anlar
• Genel kültür
• Eğitici materyal
• Keşfetmeye değer

Bilgi paylaşımı için abone olun. {call_to_action}"""
    ]
}

CALL_TO_ACTIONS = [
    "Videoyu beğendiyseniz like atmayı ve kanala abone olmayı unutmayın!",
    "Daha fazla içerik için kanala abone olun ve bildirimleri açın!",
    "Beğendiyseniz paylaşın ve arkadaşlarınızla bu içeriği keşfedin!",
    "Abone olun, like atın ve yorum yaparak düşüncelerinizi paylaşın!",
    "Kanala destek olmak için like ve paylaşım yapmayı unutmayın!"
]


def generate_seo_title(base_title: str, content_type: str = "genel") -> str:
    """
    Base başlığına dinamik SEO varyasyonları ekler.

    Args:
        base_title: Orijinal başlık
        content_type: İçerik tipi (meditasyon, motivasyon, komik, vb.)

    Returns:
        SEO optimize edilmiş başlık
    """
    modifiers = TITLE_MODIFIERS.get(content_type, TITLE_MODIFIERS["genel"])
    selected_modifier = random.choice(modifiers)

    # Base başlık çok uzunsa kısalt
    if len(base_title) > 40:
        base_title = base_title[:40] + "..."

    # Emoji ekle
    emojis = {
        "meditasyon": "🧘‍♀️",
        "motivasyon": "💪",
        "komik": "😂",
        "tarih": "📜",
        "kedi": "🐱",
        "futbol": "⚽",
        "viral": "🔥",
        "duygusal": "❤️",
        "dramatik": "😱",
        "genel": "🎯"
    }
    emoji = emojis.get(content_type, "🎬")

    # Başlığı oluştur
    seo_title = f"{emoji} {base_title} | {selected_modifier}"

    # YouTube başlık limiti (100 karakter)
    if len(seo_title) > 100:
        seo_title = seo_title[:97] + "..."

    return seo_title


def generate_seo_description(
    base_title: str,
    content_type: str = "genel",
    custom_hashtags: List[str] = None
) -> str:
    """
    SEO optimize edilmiş dinamik açıklama oluşturur.

    Args:
        base_title: Video başlığı
        content_type: İçerik tipi
        custom_hashtags: Özel hashtag'ler (opsiyonel)

    Returns:
        SEO açıklaması
    """
    # Şablon seç
    templates = DESCRIPTION_TEMPLATES.get(content_type, DESCRIPTION_TEMPLATES["genel"])
    template = random.choice(templates)

    # SEO başlık varyasyonu
    title_modifier = random.choice(TITLE_MODIFIERS.get(content_type, TITLE_MODIFIERS["genel"]))

    # Hashtag'leri seç
    available_hashtags = SEO_HASHTAGS.get(content_type, SEO_HASHTAGS["genel"])
    selected_hashtags = random.sample(available_hashtags, min(4, len(available_hashtags)))

    # Özel hashtag'leri ekle
    if custom_hashtags:
        selected_hashtags.extend(custom_hashtags)

    # Hashtag string'i oluştur
    hashtag_string = " ".join(selected_hashtags)

    # CTA seç
    call_to_action = random.choice(CALL_TO_ACTIONS)

    # Şablonu doldur
    description = template.format(
        title_modifier=title_modifier,
        hashtags=hashtag_string,
        call_to_action=call_to_action
    )

    # YouTube açıklama limiti (5000 karakter)
    if len(description) > 5000:
        description = description[:4970] + "..."

    return description


def generate_seo_tags(content_type: str = "genel", topic_keywords: List[str] = None) -> List[str]:
    """
    SEO optimize edilmiş etiket listesi oluşturur.

    Args:
        content_type: İçerik tipi
        topic_keywords: Konu özelinde anahtar kelimeler

    Returns:
        Etiket listesi
    """
    # İçerik tipine göre hashtag'leri etiket olarak kullan
    hashtags = SEO_HASHTAGS.get(content_type, SEO_HASHTAGS["genel"])

    # Hashtag'lerden # işaretini kaldır
    tags = [tag.replace("#", "") for tag in hashtags]

    # Konu anahtar kelimelerini ekle
    if topic_keywords:
        tags.extend(topic_keywords)

    # Genel etiketler
    general_tags = ["shorts", "viral", "trend", "keşfet", "fyp"]
    tags.extend(general_tags)

    # Unique ve limited liste
    unique_tags = list(set(tags))
    return unique_tags[:500]  # YouTube limiti


def upload_to_youtube(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    content_type: str = "genel",
    category_id: str = cfg.YOUTUBE_CATEGORY_ID,
    privacy: str = cfg.YOUTUBE_PRIVACY,
) -> Optional[str]:
    """
    YouTube'a video yükler ve SEO optimizasyonu uygular.

    ⚠️  ŞU AN DEVRE DIŞI — cfg.YOUTUBE_UPLOAD_ENABLED = False

    Aktifleştirmek için:
    1. Google Cloud Console'dan OAuth2 credentials.json indir
       → https://console.cloud.google.com/apis/credentials
       → YouTube Data API v3'ü etkinleştir
       → OAuth2 Client ID oluştur (Desktop App)
       → credentials.json olarak youtube_automation/ klasörüne kaydet

    2. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

    3. config.py'de YOUTUBE_UPLOAD_ENABLED = True yap

    Args:
        video_path:   Yüklenecek .mp4 dosyası
        title:        Orijinal video başlığı
        description:  Orijinal video açıklaması
        tags:         Orijinal etiketler
        content_type: İçerik tipi (SEO için kullanılır)
        category_id:  YouTube kategori ID (24 = Entertainment)
        privacy:      "public" / "private" / "unlisted"

    Returns:
        Yüklenen video ID'si veya None
    """
    if not cfg.YOUTUBE_UPLOAD_ENABLED:
        logger.info("ℹ️  YouTube yükleme devre dışı (YOUTUBE_UPLOAD_ENABLED=False)")
        logger.info(f"   Video kaydedildi: {video_path}")
        logger.info(f"   SEO Başlık: {generate_seo_title(title, content_type)}")
        logger.info(f"   SEO Açıklama: {generate_seo_description(title, content_type)[:100]}...")
        return None

    # SEO optimizasyonu uygula
    seo_title = generate_seo_title(title, content_type)
    seo_description = generate_seo_description(title, content_type)
    seo_tags = generate_seo_tags(content_type, tags)

    # ─── Gerçek yükleme kodu (credentials.json gerektirir) ───
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
        CREDS_FILE  = Path(__file__).parent.parent / "credentials.json"
        TOKEN_FILE  = Path(__file__).parent.parent / "token.json"

        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDS_FILE.exists():
                    logger.error(f"credentials.json bulunamadı: {CREDS_FILE}")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)

        # Metadata (SEO optimize edilmiş)
        body = {
            "snippet": {
                "title":       seo_title[:100],
                "description": seo_description[:5000],
                "tags":        seo_tags[:500],   # YouTube tag limiti
                "categoryId":  category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Yükle
        logger.info(f"📤 YouTube'a yükleniyor: '{seo_title[:50]}...'")
        logger.info(f"   SEO Başlık: {seo_title}")
        logger.info(f"   SEO Hashtag'ler: {[tag for tag in seo_tags if tag.startswith('#')][:5]}...")

        media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"  Yükleme: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        if video_id:
            url = f"https://www.youtube.com/shorts/{video_id}"
            logger.info(f"✅ Yüklendi: {url}")
            logger.info(f"   Final Başlık: {seo_title}")
            logger.info(f"   Final Açıklama: {seo_description[:150]}...")
            return video_id
        else:
            logger.error(f"Video ID alınamadı: {response}")
            return None

    except ImportError:
        logger.error(
            "Google API kütüphaneleri yüklü değil!\n"
            "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )
        return None
    except Exception as e:
        logger.error(f"YouTube yükleme hatası: {e}")
        return None


if __name__ == "__main__":
    # Set UTF-8 encoding for Windows terminal
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("""
YouTube Yükleme ve SEO Optimizasyonu Kurulumu:
─────────────────────────────────────────
1. https://console.cloud.google.com/apis/credentials adresine git
2. YouTube Data API v3'ü etkinleştir
3. OAuth2 Client ID oluştur (Desktop Application)
4. credentials.json olarak youtube_automation/ klasörüne kaydet
5. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
6. config.py'de YOUTUBE_UPLOAD_ENABLED = True yap

SEO Özellikleri:
• Dinamik başlık varyasyonları (her video için farklı)
• İçerik tipine özel hashtag'ler
• Otomatik 2-3 paragraflık SEO açıklamaları
• İçerik tipine göre optimize edilmiş etiketler
""")

    # Test
    test_title = "Derin Uyku Meditasyonu"
    test_type = "meditasyon"

    print(f"\nTest Başlık: {test_title}")
    print(f"Test Tip: {test_type}")
    print(f"\nSEO Başlık: {generate_seo_title(test_title, test_type)}")
    print(f"\nSEO Açıklama:\n{generate_seo_description(test_title, test_type)}")
    print(f"\nSEO Etiketler: {generate_seo_tags(test_type)}")