import urllib.request
try:
    req = urllib.request.Request("http://localhost:8080/dictionary")
    with urllib.request.urlopen(req) as response:
        print(response.read().decode("utf-8"))
except Exception as e:
    print(f"Error: {e}")
