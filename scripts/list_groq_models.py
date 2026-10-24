
import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

try:
    models = client.models.list()
    print("Available Groq models:")
    for model in models.data:
        print(model.id)
except Exception as error:
    print(f"{type(error).__name__}: {error}")
