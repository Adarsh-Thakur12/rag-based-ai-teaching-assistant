import requests


OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "bge-m3"


def create_embedding(text: str) -> list[float]:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": text
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["embedding"]