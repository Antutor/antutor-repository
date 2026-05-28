import httpx
import uuid
import re
from config import AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_REGION, ENABLE_KOREAN_TRANSLATION

_AZURE_ENDPOINT = "https://api.cognitive.microsofttranslator.com/translate"

# -----------------------------------------------------------------------
# 연소 경제 용어 보호 사전 (에저 번역기가 잘못 번역하는 복합어 보호)
# Azure Translator가 "cost-push" 등을 "비용 밀어" 등으로 직역하는 문제 해결
# -----------------------------------------------------------------------
_BASE_TERMS: dict[str, str] = {
    # --- 복합어 ---
    "cost-push inflation": "비용 인상 인플레이션",
    "demand-pull inflation": "수요 견인 인플레이션",
    "purchasing power parity": "구매력 평가",
    "consumer price index": "소비자물가지수",
    "producer price index": "생산자물가지수",
    "gross domestic product (gdp)": "국내총생산(GDP)",
    "gross domestic product": "국내총생산",
    "nominal interest rate": "명목 금리",
    "real interest rate": "실질 금리",
    "unemployment rate": "실업률",
    "exchange rate": "환율",
    "money supply": "통화량",
    "aggregate demand": "총수요",
    "aggregate supply": "총공급",
    "trade balance": "무역수지",
    "interest rate": "금리",
    "monetary policy": "통화정책",
    "fiscal policy": "재정정책",
    "quantitative easing": "양적 완화",
    "stagflation": "스태그플레이션",
    "hyperinflation": "초인플레이션",
    "deflation": "디플레이션",
    "disinflation": "디스인플레이션",
    "phillips curve": "필립스 곡선",
    "okun's law": "오쿤의 법칙",
}

_TERM_PROTECTION: dict[str, str] = {}
for _term, _ko_term in _BASE_TERMS.items():
    _TERM_PROTECTION[_term] = _ko_term
    # 복수형 자동 추가
    if _term.endswith("y"):
        _plural = _term[:-1] + "ies"
    elif _term.endswith(("s", "x", "z", "ch", "sh")):
        _plural = _term + "es"
    else:
        _plural = _term + "s"
    _TERM_PROTECTION[_plural] = _ko_term

# 부분 치환을 방지하기 위해 단어 길이 역순(긴 단어 우선 매칭)으로 정렬
_TERM_PROTECTION = dict(sorted(_TERM_PROTECTION.items(), key=lambda item: len(item[0]), reverse=True))

def _protect_terms(text: str) -> tuple[str, dict[str, str]]:
    """경제 용어를 플레이스홀더로 치환하여 번역 보호. 치환 맵 반환."""
    replacements: dict[str, str] = {}
    result = text
    for i, (term, _) in enumerate(_TERM_PROTECTION.items()):
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(result):
            placeholder = f"__TERM{i}__"
            replacements[placeholder] = _TERM_PROTECTION[term]
            result = pattern.sub(placeholder, result)
    return result, replacements

def _restore_terms(text: str, replacements: dict[str, str]) -> str:
    """플레이스홀더를 올바른 한국어 용어로 복원."""
    for placeholder, ko_term in replacements.items():
        text = text.replace(placeholder, ko_term)
        text = text.replace(placeholder.lower(), ko_term)
        # 만약 기존 괄호 방식([[]])의 잔재로 인해 ']'가 붙어있을 경우를 대비한 추가 제거
        text = text.replace(ko_term + "]", ko_term)
    return text

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

    # 경제 복합어 보호 (Azure가 직역하는 용어를 플레이스홀더로 치환)
    protected_text, replacements = _protect_terms(text)

    params = {"api-version": "3.0", "from": "en", "to": "ko"}
    body = [{"text": protected_text}]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                _AZURE_ENDPOINT, headers=_azure_headers(), params=params, json=body, timeout=10.0
            )
            response.raise_for_status()
            translated = response.json()[0]["translations"][0]["text"]
            return _restore_terms(translated, replacements)
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
