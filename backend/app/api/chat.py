from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services.chat_service import (
    create_chat_session,
    get_messages,
    get_recent_messages,
    get_session,
    save_message
)
from app.services.retrieval import retrieve_chunks
from app.services.generation import generate_answer


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    question: str
    lecture_id: str | None = None
    session_id: str | None = None
    


@router.post("")
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    # --------------------------------------------------
    # Get or create chat session
    # --------------------------------------------------

    if request.session_id:

        session = get_session(
            session_id=request.session_id,
            user_id=user_id
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        session_id = session["id"]
        lecture_id = session["lecture_id"]

        if (
            request.lecture_id is not None
            and request.lecture_id != lecture_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Lecture does not match the chat session"
            )

    else:

        session = create_chat_session(
            user_id=user_id,
            lecture_id=request.lecture_id
        )

        session_id = session["id"]
        lecture_id = request.lecture_id

    # --------------------------------------------------
    # Load previous conversation BEFORE saving
    # current user message
    # --------------------------------------------------

    history = get_recent_messages(
        session_id=session_id,
        user_id=user_id,
        limit=6
    )

    if history is None:
        history = []

    # --------------------------------------------------
    # Save current user message
    # --------------------------------------------------

    save_message(
        session_id=session_id,
        role="user",
        content=request.question
    )

    # --------------------------------------------------
    # Retrieve relevant lecture chunks
    # --------------------------------------------------

    chunks = retrieve_chunks(
        query=request.question,
        user_id=user_id,
        lecture_id=lecture_id,
        top_k=5
    )

    if not chunks:

        answer = (
            "I couldn't find the answer in the provided lectures."
        )

        save_message(
            session_id=session_id,
            role="assistant",
            content=answer
        )

        return {
            "session_id": session_id,
            "answer": answer,
            "sources": []
        }

    # --------------------------------------------------
    # Build RAG context
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Generate answer using previous conversation
    # --------------------------------------------------

    answer = generate_answer(
        question=request.question,
        context=context,
        history=history
    )

    # --------------------------------------------------
    # Save assistant response
    # --------------------------------------------------

    save_message(
        session_id=session_id,
        role="assistant",
        content=answer
    )

    # --------------------------------------------------
    # Return answer + sources
    # --------------------------------------------------

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
        "session_id": session_id,
        "answer": answer,
        "sources": sources
    }


@router.get("/sessions/{session_id}")
def get_chat_history(
    session_id: str,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    messages = get_messages(
        session_id=session_id,
        user_id=user_id
    )

    if messages is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found"
        )

    return {
        "session_id": session_id,
        "messages": messages
    }