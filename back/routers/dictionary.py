from fastapi import APIRouter, HTTPException
from config import CONCEPT_DICTIONARY
from services.translator import translate_en_to_ko

router = APIRouter()

@router.get("/dictionary")
async def get_all_dictionary_terms():
    translated_terms = []
    for k in CONCEPT_DICTIONARY.keys():
        translated = await translate_en_to_ko(k)
        translated_terms.append(translated)
    return translated_terms

@router.get("/dictionary/{term}")
async def get_dictionary_term(term: str):
    target_key = None
    
    # 1. 대소문자 구분 없이 원본 영어 키로 먼저 검색 시도
    for k in CONCEPT_DICTIONARY.keys():
        if k.lower() == term.lower():
            target_key = k
            break
            
    # 2. 만약 영어로 못 찾았다면, 프론트엔드가 넘긴 값이 '한국어 번역본'일 경우를 대비해 매칭 시도
    if not target_key:
        for k in CONCEPT_DICTIONARY.keys():
            translated_k = await translate_en_to_ko(k)
            if term == translated_k or term == translated_k.replace(" ", ""):
                target_key = k
                break
                
    if not target_key:
        error_msg = await translate_en_to_ko("Term not found in dictionary.")
        raise HTTPException(status_code=404, detail=error_msg)
        
    data = CONCEPT_DICTIONARY[target_key].copy()
    data["term"] = await translate_en_to_ko(data["term"])
    data["simple_definition"] = await translate_en_to_ko(data["simple_definition"])
    data["example"] = await translate_en_to_ko(data["example"])
    
    return data
