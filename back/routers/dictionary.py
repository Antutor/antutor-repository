from fastapi import APIRouter, HTTPException
from config import CONCEPT_DICTIONARY

router = APIRouter()

@router.get("/dictionary")
async def get_all_dictionary_terms():
    return list(CONCEPT_DICTIONARY.keys())

@router.get("/dictionary/{term}")
async def get_dictionary_term(term: str):
    if term not in CONCEPT_DICTIONARY:
        raise HTTPException(status_code=404, detail="Term not found in dictionary.")
    return CONCEPT_DICTIONARY[term]
