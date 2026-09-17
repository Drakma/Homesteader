import os
from google import genai

key = None
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('GEMINI_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")

client = genai.Client(api_key=key)

prompt = "A 3D low-poly faceted render of a brass ball valve with blue handle floating on solid dark slate background."

for m in ['imagen-3.0-generate-002', 'imagen-3.0-generate-001', 'imagen-4.0-generate-001']:
    print(f"\n--- Testing generate_images with {m} ---")
    try:
        result = client.models.generate_images(
            model=m,
            prompt=prompt,
            config=dict(number_of_images=1, aspect_ratio="1:1")
        )
        print("Success! Generated images count:", len(result.generated_images))
        with open(f"test_{m}.png", "wb") as f_out:
            f_out.write(result.generated_images[0].image.image_bytes)
        print(f"Successfully saved test_{m}.png!")
        exit(0)
    except Exception as e:
        print(f"Error with {m}:", e)

