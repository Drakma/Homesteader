from huggingface_hub import HfApi

api = HfApi()
spaces = list(api.list_spaces(search="trellis", limit=10))
print("TRELLIS spaces:")
for s in spaces:
    print(f" - {s.id} (likes: {s.likes})")

spaces_im = list(api.list_spaces(search="InstantMesh", limit=5))
print("\nInstantMesh spaces:")
for s in spaces_im:
    print(f" - {s.id} (likes: {s.likes})")

spaces_tripo = list(api.list_spaces(search="TripoSR", limit=5))
print("\nTripoSR spaces:")
for s in spaces_tripo:
    print(f" - {s.id} (likes: {s.likes})")

