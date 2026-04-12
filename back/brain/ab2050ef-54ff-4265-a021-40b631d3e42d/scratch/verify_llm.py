import os
import sys

# Ensure local imports work
sys.path.append(os.getcwd() + "/back")

from multi_agent.llm_config import draft_llm, debate_llm, synthesis_llm
from config import DRAFT_LLM_MODEL, DEBATE_LLM_MODEL

def verify_config():
    print("--- LLM Configuration Verification ---")
    print(f"DRAFT_LLM_MODEL: {DRAFT_LLM_MODEL}")
    print(f"DEBATE_LLM_MODEL: {DEBATE_LLM_MODEL}")
    
    print("\n--- LLM Instance Sanity Check ---")
    print(f"draft_llm: model={draft_llm.model}, temp={draft_llm.temperature}")
    print(f"debate_llm: model={debate_llm.model}, temp={debate_llm.temperature}")
    print(f"synthesis_llm: model={synthesis_llm.model}, temp={synthesis_llm.temperature}")
    
    # Assertions for internal validation
    assert draft_llm.model == DRAFT_LLM_MODEL, "Draft model mismatch"
    assert debate_llm.model == DEBATE_LLM_MODEL, "Debate model mismatch"
    assert synthesis_llm.model == DEBATE_LLM_MODEL, "Synthesis model mismatch"
    assert draft_llm.temperature == 0.0, "Draft temperature should be 0.0"
    
    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    verify_config()
