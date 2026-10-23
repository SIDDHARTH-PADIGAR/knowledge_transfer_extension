
import os
import urllib.request
import urllib.error

request = urllib.request.Request(
    "https://api.groq.com/openai/v1/models",
    headers={
    "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
    "User-Agent": "knowledge-transfer-prototype/1.0",
},
)

try:
    with urllib.request.urlopen(request, timeout=20) as response:
        print("HTTP:", response.status)
        print("Groq authentication: PASS")
except urllib.error.HTTPError as error:
    print("HTTP:", error.code)
    print(error.read().decode("utf-8")[:2000])
except Exception as error:
    print(type(error).__name__, str(error))
