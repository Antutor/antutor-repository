import requests
import json
import uuid

payload = {
    "session_id": str(uuid.uuid4()),
    "user_id": str(uuid.uuid4()),
    "concept": "인플레이션",
    "is_pre_test": False,
    "answers": [
        {
            "question_id": 1,
            "selected_choice": 1,
            "confidence_level": 1
        }
    ]
}

try:
    res = requests.post("http://localhost:8080/quiz/submit", json=payload)
    print("Status Code:", res.status_code)
    print("Response JSON:", res.json())
except Exception as e:
    print("Error:", e)
