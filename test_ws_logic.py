import sys
import json
import asyncio
from back.services.translator import translate_en_to_ko

async def main():
    with open("back/logs/debate_logs.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
        last_line = lines[-1]
    
    final_state = json.loads(last_line)
    
    expert_results = []
    expert_scores_raw = {"The Academic Auditor": 0.7, "The Market Practitioner": 0.2, "The Macro-Connector": 0.1}
    for persona, review in final_state.get("draft_reviews", {}).items():
        expert_results.append({
            "persona": persona,
            "score": expert_scores_raw.get(persona, 0.75),
            "feedback": review,
            "is_fallback": False
        })
    
    for expert in expert_results:
        raw_feedback = expert.get("feedback")
        print(f"[{expert['persona']}] raw_feedback type: {type(raw_feedback)}")
        if isinstance(raw_feedback, dict):
            actual_text = raw_feedback.get("weakest_point", raw_feedback.get("feedback", ""))
            print(f"  actual_text: {repr(actual_text)}")
            translated = await translate_en_to_ko(actual_text) if actual_text else ""
            print(f"  translated: {repr(translated)}")
            expert["feedback"] = translated
        elif isinstance(raw_feedback, str):
            expert["feedback"] = await translate_en_to_ko(raw_feedback)
            
    print("\nFINAL expert_results:")
    print(json.dumps(expert_results, indent=2, ensure_ascii=False))

asyncio.run(main())
