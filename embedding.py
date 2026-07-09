import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"

def get_embedding(text):

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen3-embedding",
                "prompt": text
            },
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        if "embedding" not in data:
            print("OLLAMA RESPONSE:", data)
            return None

        return data["embedding"]

    except Exception as e:
        print("=" * 60)
        print("EMBEDDING ERROR")
        print(type(e).__name__)
        print(e)
        print("=" * 60)
        return None