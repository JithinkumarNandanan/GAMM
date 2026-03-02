import requests
import os

ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
try:
    response = requests.get(f"{ollama_url}/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("Available Ollama models:")
        for m in models:
            print(f"  - {m.get('name', 'unknown')}")
        if not models:
            print("  (no models found)")
    else:
        print(f"Error: Ollama returned status {response.status_code}")
except Exception as e:
    print(f"Error connecting to Ollama: {e}")
    print("Make sure Ollama is running: ollama serve")
