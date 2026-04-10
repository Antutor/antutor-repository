from fastapi import APIRouter, HTTPException
from database import supabase
from services.translator import translate_en_to_ko

router = APIRouter()

@router.get("/dictionary")
async def get_all_dictionary_terms():
    translated_terms = []
    response = supabase.table("concepts").select("name").execute()
    for row in response.data:
        translated = await translate_en_to_ko(row["name"])
        translated_terms.append(translated)
    return translated_terms

@router.get("/dictionary/{term}")
async def get_dictionary_term(term: str):
    response = supabase.table("concepts").select("*").execute()
    concepts = response.data
    
    target_concept = None
    
    # 1. 대소문자 구분 없이 원본 영어 키로 먼저 검색 시도
    for row in concepts:
        if row["name"].lower() == term.lower():
            target_concept = row
            break
            
    # 2. 만약 영어로 못 찾았다면, 프론트엔드가 넘긴 값이 '한국어 번역본'일 경우를 대비해 매칭 시도
    if not target_concept:
        for row in concepts:
            translated_k = await translate_en_to_ko(row["name"])
            if term == translated_k or term == translated_k.replace(" ", ""):
                target_concept = row
                break
                
    if not target_concept:
        error_msg = await translate_en_to_ko("Term not found in dictionary.")
        raise HTTPException(status_code=404, detail=error_msg)
        
    term_str = await translate_en_to_ko(target_concept["name"])
    def_str = await translate_en_to_ko(target_concept.get("definition") or "")
    
    return {
        "term": term_str,
        "simple_definition": def_str,
        "example": ""
    }
