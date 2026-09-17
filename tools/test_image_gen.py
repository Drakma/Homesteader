import os
from google import genai
from google.genai import types

key = None
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('GEMINI_API_KEY=') and not line.startswith('#'):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")

client = genai.Client(api_key=key)

prompt = """
A 3D low-poly faceted render of a brass ball valve with blue lever handle.
Style: clean video game asset icon, low-poly 3D model with visible geometric facets, ambient occlusion, smooth matte and satin materials, faceted specular highlights.
View: isometric 3/4 front view, floating centered in empty space.
Lighting: soft studio key lighting from top-left, clean edge lighting, no cast shadows on floor, no pedestal, no table.
Background: solid uniform dark slate background (hex #2b3442), completely plain and flat, no gradient, no patterns, no borders, no cards, no square frames, no UI elements.
"""

print("Testing image generation with gemini-2.5-flash-image / gemini-3.1-flash-image...")

models_to_test = [
    'gemini-3.1-flash-image',
    'gemini-3-pro-image',
    'gemini-3.1-flash-lite-image'
]

for m in models_to_test:
    print(f"\n--- Testing model: {m} ---")
    try:
        response = client.models.generate_content(
            model=m,
            contents=prompt
        )
        print("Response received! Parts count:", len(response.candidates[0].content.parts))
        for i, p in enumerate(response.candidates[0].content.parts):
            if p.inline_data:
                print(f"Part {i} has image data! Bytes:", len(p.inline_data.data))
                with open(f"test_{m.replace('/', '_')}.png", "wb") as f_out:
                    f_out.write(p.inline_data.data)
                print(f"Saved test_{m.replace('/', '_')}.png!")
                exit(0)
    except Exception as e:
        print(f"Error with {m}:", e)
