import urllib.request
import json
import traceback

try:
    req = urllib.request.Request("http://localhost:8080/dictionary?language=ko")
    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read().decode("utf-8")
        with open("scratch_response.json", "w", encoding="utf-8") as f:
            f.write(content)
        print("Success! Response written to scratch_response.json")
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    with open("scratch_error.txt", "w", encoding="utf-8") as f:
        f.write(e.read().decode("utf-8"))
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
