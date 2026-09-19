from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services.retrieval import retrieve_chunks
from app.services.generation import generate_answer


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str
    lecture_id: str | None = None


@router.post("")
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    chunks = retrieve_chunks(
        query=request.question,
        user_id=user_id,
        lecture_id=request.lecture_id,
        top_k=5
    )

    if not chunks:
        return {
            "answer": "I couldn't find the answer in the provided lectures.",
            "sources": []
        }

    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"""
Lecture chunk:
{chunk["content"]}

Timestamp:
{chunk["start_time"]} - {chunk["end_time"]}
"""
        )

    context = "\n".join(context_parts)

    answer = generate_answer(
        question=request.question,
        context=context
    )

    sources = [
        {
            "lecture_id": chunk["lecture_id"],
            "start_time": chunk["start_time"],
            "end_time": chunk["end_time"],
            "content": chunk["content"],
            "similarity": chunk["similarity"]
        }
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "sources": sources
    }