import httpx
from config import DEEPL_API_KEY, ENABLE_KOREAN_TRANSLATION

async def translate_en_to_ko(text: str) -> str:
    """
    Translates English text to Korean using the DeepL Free API.
    If ENABLE_KOREAN_TRANSLATION is False, or DEEPL_API_KEY is missing, or an error occurs, 
    the original English text is returned (Fall-back).
    """
    if not ENABLE_KOREAN_TRANSLATION or not text or not DEEPL_API_KEY:
        return text

    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": [text],
        "target_lang": "KO"
    }
    
    # httpx를 통해 비동기로 API 전송
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data["translations"][0]["text"]
        except Exception as e:
            print(f"DeepL Translation Error (EN->KO): {e}")
            return text  # 에러 발생 시 원문(영어)을 그대로 반환하여 시스템 다운 방지

async def translate_ko_to_en(text: str) -> str:
    """
    Translates Korean text to English using the DeepL Free API.
    Used for translating user inputs before they hit the English LLM pipeline.
    """
    if not ENABLE_KOREAN_TRANSLATION or not text or not DEEPL_API_KEY:
        return text

    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": [text],
        "target_lang": "EN-US"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data["translations"][0]["text"]
        except Exception as e:
            print(f"DeepL Translation Error (KO->EN): {e}")
            return text

