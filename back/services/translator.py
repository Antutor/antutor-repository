import httpx
import uuid
from config import AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_REGION, ENABLE_KOREAN_TRANSLATION

_AZURE_ENDPOINT = "https://api.cognitive.microsofttranslator.com/translate"

def _azure_headers() -> dict:
    return {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

async def translate_en_to_ko(text: str, target_lang: str = "ko") -> str:
    """
    Translates English text to Korean using Azure Cognitive Services Translator.
    If ENABLE_KOREAN_TRANSLATION is False, AZURE_TRANSLATOR_KEY is missing,
    or an error occurs, the original text is returned (fall-back).
    """
    if not ENABLE_KOREAN_TRANSLATION or not text or not AZURE_TRANSLATOR_KEY or target_lang.lower() != "ko":
        return text

    params = {"api-version": "3.0", "from": "en", "to": "ko"}
    body = [{"text": text}]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                _AZURE_ENDPOINT, headers=_azure_headers(), params=params, json=body, timeout=10.0
            )
            response.raise_for_status()
            return response.json()[0]["translations"][0]["text"]
        except Exception as e:
            print(f"Azure Translation Error (EN->KO): {e}")
            return text  # 에러 발생 시 원문(영어) 반환하여 시스템 다운 방지


async def translate_list_en_to_ko(texts: list[str], target_lang: str = "ko") -> list[str]:
    """
    Translates a list of English strings to Korean in a single Azure Translator API call.
    """
    if not ENABLE_KOREAN_TRANSLATION or not texts or not AZURE_TRANSLATOR_KEY or target_lang.lower() != "ko":
        return texts

    params = {"api-version": "3.0", "from": "en", "to": "ko"}
    body = [{"text": t} for t in texts]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                _AZURE_ENDPOINT, headers=_azure_headers(), params=params, json=body, timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
            return [item["translations"][0]["text"] for item in data]
        except Exception as e:
            print(f"Azure Batch Translation Error: {e}")
            return texts


async def translate_ko_to_en(text: str, source_lang: str = "ko") -> str:
    """
    Translates Korean text to English using Azure Cognitive Services Translator.
    Used for translating user inputs before they hit the English LLM pipeline.
    """
    if not ENABLE_KOREAN_TRANSLATION or not text or not AZURE_TRANSLATOR_KEY or source_lang.lower() != "ko":
        return text

    params = {"api-version": "3.0", "from": "ko", "to": "en"}
    body = [{"text": text}]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                _AZURE_ENDPOINT, headers=_azure_headers(), params=params, json=body, timeout=10.0
            )
            response.raise_for_status()
            return response.json()[0]["translations"][0]["text"]
        except Exception as e:
            print(f"Azure Translation Error (KO->EN): {e}")
            return text
