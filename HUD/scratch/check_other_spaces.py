from gradio_client import Client

print("Checking InstantMesh API...")
client_im = Client("TencentARC/InstantMesh")
client_im.view_api()

print("\nChecking TripoSR API...")
client_tsr = Client("stabilityai/TripoSR")
client_tsr.view_api()

