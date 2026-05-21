from fastapi import APIRouter, HTTPException
from database import supabase
from services.translator import translate_en_to_ko, translate_list_en_to_ko

router = APIRouter()

@router.get("/debug_schema")
async def debug_schema():
    response = supabase.table("concepts").select("*").limit(1).execute()
    return response.data

@router.get("/dictionary")
async def get_all_dictionary_terms(language: str = "ko"):
    """
    Fetches all concepts from Supabase.
    If language='ko', translates names and definitions via DeepL batch call.
    If language='en', returns original English text directly.
    """
    response = supabase.table("concepts").select("name, definition, category").execute()
    concepts = response.data

    if not concepts:
        return []

    if language != "ko":
        # Return raw English directly — no translation needed
        return [
            {
                "term": row["name"],
                "simple_definition": row.get("definition") or "",
                "original_name": row["name"],
                "example": "",
                "category": row.get("category", "academic")
            }
            for row in concepts
        ]

    # Korean: batch-translate with DeepL
    to_translate = []
    for row in concepts:
        to_translate.append(row["name"])
        to_translate.append(row.get("definition") or "")

    translated_list = await translate_list_en_to_ko(to_translate)

    results = []
    for i in range(len(concepts)):
        results.append({
            "term": translated_list[i*2],
            "simple_definition": translated_list[i*2 + 1],
            "original_name": concepts[i]["name"],
            "example": "",
            "category": concepts[i].get("category", "academic")
        })

    return results

@router.get("/dictionary/{term}")
async def get_dictionary_term(term: str, language: str = "ko"):
    """
    Fetches a single concept by term name (English or Korean).
    """
    response = supabase.table("concepts").select("*").execute()
    concepts = response.data

    target_concept = None

    # 1. Try matching with original English name
    for row in concepts:
        if row["name"].lower() == term.lower():
            target_concept = row
            break

    # 2. If not found and language is Korean, try Korean name matching
    if not target_concept and language == "ko":
        names = [row["name"] for row in concepts]
        translated_names = await translate_list_en_to_ko(names)

        for idx, trans_name in enumerate(translated_names):
            if term == trans_name or term == trans_name.replace(" ", ""):
                target_concept = concepts[idx]
                break

    if not target_concept:
        raise HTTPException(status_code=404, detail="Term not found in dictionary.")

    if language != "ko":
        return {
            "term": target_concept["name"],
            "simple_definition": target_concept.get("definition") or "",
            "example": "",
            "category": target_concept.get("category", "academic")
        }

    final_translations = await translate_list_en_to_ko([target_concept["name"], target_concept.get("definition") or ""])

    return {
        "term": final_translations[0],
        "simple_definition": final_translations[1],
        "example": "",
        "category": target_concept.get("category", "academic")
    }
