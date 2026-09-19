import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


def generate_answer(
    question: str,
    context: str
) -> str:

    prompt = f"""
You are an AI teaching assistant.

Answer the user's question using ONLY the provided lecture context.

If the answer cannot be found in the context, say:
"I couldn't find the answer in the provided lectures."

Do not make up information.

Lecture context:
{context}

Question:
{question}

Answer:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["response"].strip()