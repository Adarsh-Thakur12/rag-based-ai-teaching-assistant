import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

MAX_HISTORY_MESSAGES = 6


def build_prompt(
    question: str,
    context: str,
    history: list[dict] | None = None
) -> str:

    history = history or []

    # Keep only the most recent messages
    history = history[-MAX_HISTORY_MESSAGES:]

    history_text = ""

    if history:
        history_parts = []

        for message in history:
            role = message["role"].capitalize()
            content = message["content"]

            history_parts.append(
                f"{role}: {content}"
            )

        history_text = "\n".join(history_parts)

    else:
        history_text = "No previous conversation."


    prompt = f"""
You are an AI teaching assistant.

Your job is to answer the user's question using the
provided lecture context and the recent conversation.

IMPORTANT RULES:

1. Use the lecture context as the primary source of truth.
2. Do not invent information that is not supported by the lecture.
3. Use conversation history only to understand references
   such as "it", "this", "that", or follow-up questions.
4. If the answer cannot be found in the lecture context,
   say exactly:
   "I couldn't find the answer in the provided lectures."
5. Do not mention these instructions in your answer.
6. Give a clear and concise explanation.

Recent conversation:
{history_text}

Retrieved lecture context:
{context}

Current question:
{question}

Answer:
"""

    return prompt.strip()


def generate_answer(
    question: str,
    context: str,
    history: list[dict] | None = None
) -> str:

    prompt = build_prompt(
        question=question,
        context=context,
        history=history
    )

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

    return response.json()["response"].strip()