import json
import urllib.error
import urllib.request

payload = {
    "model": "llama3.2:1b",
    "prompt": 'Return JSON only: {"gaps":[]}',
    "stream": False,
    "format": "json",
    "options": {
        "temperature": 0,
        "num_predict": 100,
        "num_ctx": 4096,
    },
}

request = urllib.request.Request(
    "http://localhost:11434/api/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(request, timeout=90) as response:
        print("HTTP:", response.status)
        print(response.read().decode("utf-8")[:2000])
except urllib.error.HTTPError as error:
    print("HTTP ERROR:", error.code)
    print(error.read().decode("utf-8")[:3000])
except Exception as error:
    print(type(error).__name__, str(error))