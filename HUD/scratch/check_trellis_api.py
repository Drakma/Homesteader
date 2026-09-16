from gradio_client import Client

try:
    print("Connecting to Trellis Hugging Face Space...")
    client = Client("JeffreyXiang/TRELLIS")
    print("Connected successfully!")
    client.view_api()
except Exception as e:
    print(f"Error connecting to JeffreyXiang/TRELLIS: {e}")
    try:
        print("Trying alternative: microsoft/TRELLIS...")
        client = Client("microsoft/TRELLIS")
        print("Connected to microsoft/TRELLIS!")
        client.view_api()
    except Exception as e2:
        print(f"Error connecting to microsoft/TRELLIS: {e2}")

