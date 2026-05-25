import urllib.request
import urllib.parse
import traceback

concept = urllib.parse.quote("인플레이션")
try:
    req = urllib.request.Request(f"http://localhost:8080/quiz/{concept}")
    with urllib.request.urlopen(req, timeout=10) as response:
        content = response.read().decode("utf-8")
        print("Success!")
        with open("scratch_quiz.json", "w", encoding="utf-8") as f:
            f.write(content)
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
