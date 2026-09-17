import os
from google import genai

key = None
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('GEMINI_API_KEY=') and not line.startswith('#'):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")

client = genai.Client(api_key=key)

print("Listing available models...")
try:
    for m in client.models.list():
        if 'image' in m.name.lower() or 'imagen' in m.name.lower():
            print(f" - {m.name}")
except Exception as e:
    print("Error listing models:", e)

