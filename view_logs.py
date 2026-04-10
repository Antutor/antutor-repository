import json
import sys
from pathlib import Path

def print_log_table(log_path="back/logs/debate_logs.jsonl"):
    file_path = Path(log_path)
    if not file_path.exists():
        print(f"File not found: {log_path}")
        return

    print("="*100)
    print(f"{'Time':<22} | {'Concept':<10} | {'Roles / Synthesis'}")
    print("="*100)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                time = data.get("timestamp", "")[:19]
                concept = data.get("concept", "")
                
                print(f"[{time}] | {concept:<10} | >> User: {data.get('user_answer', '')[:50]}...")
                
                print("-" * 100)
                drafts = data.get("draft_reviews", {})
                for agent, review in drafts.items():
                    print(f"[{agent}]\n{review.strip()[:100]}...\n")
                
                critiques = data.get("critiques", [])
                for i, crit in enumerate(critiques):
                    print(f"[Round {i+1} Critique]\n{crit.strip()[:100]}...\n")
                    
                print(f"[Final Synthesis]\n{data.get('final_synthesis', '').strip()[:100]}...")
                print("="*100)
                
    except Exception as e:
        print(f"Error parsing jsonl: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_log_table(sys.argv[1])
    else:
        print_log_table()
