"""
back/services/guardrail.py
==========================
보안 가드레일 — 프롬프트 인젝션 / 탈옥 시도 탐지

DB 미구축 상태: 차단 로그 저장은 print()로 임시 처리
실제 운영 시 TODO 주석 위치에 Supabase INSERT 쿼리를 추가합니다.
"""

import re
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# 위협 패턴 정의
# ---------------------------------------------------------------------------

# 1. 프롬프트 인젝션 (시스템 지시를 무시하도록 유도)
_INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"disregard\s+(your\s+)?(previous\s+)?instructions?",
    r"forget\s+(everything|all\s+instructions?|your\s+rules?)",
    r"override\s+(your\s+)?(system\s+)?prompt",
    r"new\s+instructions?\s*:",
    r"\[system\]",
    r"<\|?system\|?>",
    r"###\s*instruction",
    r"\[inst\]",
    # 한국어 인젝션
    r"이전\s+지시\s*를?\s*(무시|잊어)",
    r"지시\s*사항\s*(무시|삭제|초기화)",
    r"시스템\s*프롬프트",
]

# 2. 탈옥 / 롤플레이 우회 시도
_JAILBREAK_PATTERNS: list[str] = [
    r"\bdan\b",                        # Do Anything Now
    r"jailbreak",
    r"developer\s+mode",
    r"god\s+mode",
    r"unrestricted\s+mode",
    r"pretend\s+(you\s+are|to\s+be)\s+(an?\s+)?(?:evil|harmful|unrestricted|unfiltered)",
    r"act\s+as\s+(an?\s+)?(?:evil|harmful|uncensored|unfiltered)",
    r"you\s+are\s+now\s+(free|unrestricted|unfiltered)",
    r"bypass\s+(your\s+)?(safety|filter|restriction|guardrail)",
    r"no\s+(restriction|filter|limit|safety)",
    r"without\s+(restriction|filter|limit|safety\s+check)",
    # 한국어 탈옥
    r"제한\s*(없이|을\s*무시)",
    r"필터\s*(우회|무시|해제)",
    r"안전\s*장치\s*(무시|해제|우회)",
    r"탈옥",
]

# 3. 악의적 의도 (교육 플랫폼 범위 외 위험 요청)
_HARM_PATTERNS: list[str] = [
    r"how\s+to\s+(make|build|create)\s+(a\s+)?(bomb|weapon|malware|virus|ransomware)",
    r"(hack|exploit)\s+(into|a)\s+",
    r"(steal|leak)\s+(password|credential|data)",
    r"child\s+(porn|abuse|exploit)",
    r"(폭탄|무기|마약|해킹|악성코드|바이러스).*?(만드|제조|합성|방법|어떻게|알려)",
]

# 모든 패턴을 컴파일
_COMPILED: list[tuple[str, re.Pattern]] = []
for _label, _patterns in [
    ("prompt_injection", _INJECTION_PATTERNS),
    ("jailbreak", _JAILBREAK_PATTERNS),
    ("harmful_content", _HARM_PATTERNS),
]:
    for _p in _patterns:
        _COMPILED.append((_label, re.compile(_p, re.IGNORECASE | re.DOTALL)))


# ---------------------------------------------------------------------------
# 핵심 탐지 함수
# ---------------------------------------------------------------------------

def _detect_threat(text: str) -> tuple[bool, str]:
    """
    입력 텍스트에서 위협 패턴을 검색합니다.
    Returns:
        (is_threat: bool, threat_type: str)
    """
    for threat_type, pattern in _COMPILED:
        if pattern.search(text):
            matched = pattern.search(text).group(0)
            return True, f"{threat_type} (matched: '{matched[:50]}')"
    return False, ""


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

async def run_guardrail(user_input: str, user_id: str = "unknown") -> None:
    """
    사용자 입력을 검사하고 위협이 감지되면 HTTP 400을 발생시킵니다.
    chat.py의 LLM 파이프라인 진입 전에 호출하세요.

    Args:
        user_input: 검사할 사용자 입력 텍스트 (영어 번역본 권장)
        user_id:    로그용 사용자 식별자

    Raises:
        HTTPException(400): 위협 감지 시
    """
    is_threat, reason = _detect_threat(user_input)
    if not is_threat:
        return

    print(
        f"🚨 [Guardrail] 위협 감지 | user={user_id} | type={reason} "
        f"| input_preview='{user_input[:80]}'",
        flush=True,
    )
    # TODO: DB 로그 저장 (보안 로그 테이블 구축 후 아래 코드로 교체)
    # await supabase.table("security_logs").insert({
    #     "user_id": user_id,
    #     "threat_type": reason,
    #     "input_preview": user_input[:200],
    #     "created_at": datetime.utcnow().isoformat()
    # }).execute()
    print("📝 [Guardrail] 보안 로그 저장됨 (DB 미구축 — 임시 처리)", flush=True)

    raise HTTPException(
        status_code=400,
        detail=f"입력이 보안 정책에 의해 차단되었습니다. ({reason.split('(')[0].strip()})",
    )


async def run_guardrail_ws(user_input: str, user_id: str = "unknown") -> str | None:
    """
    WebSocket 전용 가드레일 — 예외 대신 오류 메시지를 반환합니다.
    차단 시 websocket.send_json()에 전달할 메시지를 반환하고,
    정상이면 None을 반환합니다.
    """
    is_threat, reason = _detect_threat(user_input)
    if not is_threat:
        return None

    print(
        f"🚨 [Guardrail-WS] 위협 감지 | user={user_id} | type={reason}",
        flush=True,
    )
    print("📝 [Guardrail] 보안 로그 저장됨 (DB 미구축 — 임시 처리)", flush=True)

    return f"입력이 보안 정책에 의해 차단되었습니다. ({reason.split('(')[0].strip()})"
