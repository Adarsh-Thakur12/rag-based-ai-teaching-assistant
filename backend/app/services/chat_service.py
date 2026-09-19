from app.database.supabase import supabase


def create_chat_session(
    user_id: str,
    lecture_id: str | None = None
):
    response = (
        supabase
        .table("chat_sessions")
        .insert({
            "user_id": user_id,
            "lecture_id": lecture_id
        })
        .execute()
    )

    if not response.data:
        raise Exception("Failed to create chat session")

    return response.data[0]


def save_message(
    session_id: str,
    role: str,
    content: str
):
    response = (
        supabase
        .table("chat_messages")
        .insert({
            "session_id": session_id,
            "role": role,
            "content": content
        })
        .execute()
    )

    if not response.data:
        raise Exception("Failed to save chat message")

    return response.data[0]


def get_session(
    session_id: str,
    user_id: str
):
    response = (
        supabase
        .table("chat_sessions")
        .select("id, user_id, lecture_id, created_at")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    return response.data


def get_messages(
    session_id: str,
    user_id: str
):
    session = get_session(
        session_id=session_id,
        user_id=user_id
    )

    if not session:
        return None

    response = (
        supabase
        .table("chat_messages")
        .select("id, role, content, created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )

    return response.data