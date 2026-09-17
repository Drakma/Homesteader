import os
from google import genai

key = None
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('GEMINI_API_KEY=') and not line.startswith('#'):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")

if not key or key == 'YOUR_API_KEY_HERE':
    print('Key is missing or placeholder')
    exit(1)

print(f"Key loaded: {key[:6]}...{key[-4:]} (len: {len(key)})")

client = genai.Client(api_key=key)

try:
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents='Respond with only the word SUCCESS'
    )
    print(f"API Connection Test (gemini-3.6-flash): {response.text.strip()}")
except Exception as e:
    print(f"Error testing Gemini API: {e}")
