from gradio_client import Client

candidates = [
    "trellis-community/TRELLIS",
    "TencentARC/InstantMesh",
    "stabilityai/TripoSR"
]

for c in candidates:
    try:
        print(f"Testing client for: {c}...")
        client = Client(c)
        print(f"-> SUCCESS connected to {c}!")
        client.view_api()
        break
    except Exception as e:
        print(f"-> Failed {c}: {e}")

