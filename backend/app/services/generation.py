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
    history = history[-MAX_HISTORY_MESSAGES:]

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

Answer the user's question using the retrieved lecture
context below.

IMPORTANT RULES:

1. The retrieved lecture context is the primary source
   for answering the question.

2. If the context contains information that directly or
   indirectly answers the question, use that information
   to answer the question.

3. Do not require the wording of the question to exactly
   match the wording in the lecture.

4. The user may use pronouns or references such as:
   "he", "she", "it", "this", "that", "they", etc.
   Use the recent conversation to understand these
   references when possible.

5. Do not invent facts that are not supported by the
   retrieved lecture context.

6. If the retrieved context genuinely does not contain
   enough information to answer the question, say exactly:
   "I couldn't find the answer in the provided lectures."

7. When the context provides an approximate value or time,
   clearly indicate that it is approximate.

8. Give a concise and direct answer.

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