from fastapi import APIRouter, HTTPException
from database import supabase
from services.translator import translate_en_to_ko, translate_list_en_to_ko

router = APIRouter()

@router.get("/dictionary")
async def get_all_dictionary_terms():
    """
    Fetches all concepts from Supabase and translates both names and definitions
    in a single batch request to DeepL.
    """
    response = supabase.table("concepts").select("name, definition").execute()
    concepts = response.data

    if not concepts:
        return []

    # Prepare strings for batch translation
    # We combine name and definition to translate them together or just send a flat list
    to_translate = []
    for row in concepts:
        to_translate.append(row["name"])
        to_translate.append(row.get("definition") or "")

    translated_list = await translate_list_en_to_ko(to_translate)

    # Reconstruct the response
    results = []
    for i in range(len(concepts)):
        results.append({
            "term": translated_list[i*2],
            "simple_definition": translated_list[i*2 + 1],
            "original_name": concepts[i]["name"],
            "example": ""
        })
    
    return results

@router.get("/dictionary/{term}")
async def get_dictionary_term(term: str):
    """
    Still supports fetching a single term, but the primary use case should now be /dictionary.
    """
    response = supabase.table("concepts").select("*").execute()
    concepts = response.data
    
    target_concept = None
    
    # 1. Try matching with original English name
    for row in concepts:
        if row["name"].lower() == term.lower():
            target_concept = row
            break
            
    # 2. Try matching with translated Korean name
    if not target_concept:
        # For individual search, we might still need individual translation or a smarter way
        # But to avoid N+1 here too, we could batch translate all names first
        names = [row["name"] for row in concepts]
        translated_names = await translate_list_en_to_ko(names)
        
        for idx, trans_name in enumerate(translated_names):
            if term == trans_name or term == trans_name.replace(" ", ""):
                target_concept = concepts[idx]
                break
                
    if not target_concept:
        error_msg = await translate_en_to_ko("Term not found in dictionary.")
        raise HTTPException(status_code=404, detail=error_msg)
        
    # Batch translate name and definition for the single result
    final_translations = await translate_list_en_to_ko([target_concept["name"], target_concept.get("definition") or ""])
    
    return {
        "term": final_translations[0],
        "simple_definition": final_translations[1],
        "example": ""
    }
