import { createClient } from "@/lib/supabase/client";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function getAccessToken(): Promise<string> {
  const supabase = createClient();

  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error || !session) {
    throw new Error("User is not authenticated");
  }

  return session.access_token;
}

export async function getLectures() {
  const token = await getAccessToken();

  const response = await fetch(`${API_URL}/lectures`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch lectures (${response.status})`
    );
  }

  return response.json();
}

export async function uploadLecture(
  file: File,
  title: string
) {
  const token = await getAccessToken();

  const formData = new FormData();

  formData.append("file", file);
  formData.append("title", title);

  const response = await fetch(
    `${API_URL}/lectures/upload`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    let message = `Upload failed (${response.status})`;

    try {
      const data = await response.json();

      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function sendChatMessage(
  question: string,
  lectureId: string,
  sessionId?: string
) {
  const token = await getAccessToken();

  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      lecture_id: lectureId,
      session_id: sessionId || null,
    }),
  });

  if (!response.ok) {
    let message =
      `Chat request failed (${response.status})`;

    try {
      const data = await response.json();

      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function getChatHistory(
  sessionId: string
) {
  const token = await getAccessToken();

  const response = await fetch(
    `${API_URL}/chat/sessions/${sessionId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    let message =
      `Failed to fetch chat history (${response.status})`;

    try {
      const data = await response.json();

      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}
export async function getChatSessions(
  lectureId: string
) {
  const token = await getAccessToken();

  const response = await fetch(
    `${API_URL}/chat/sessions?lecture_id=${encodeURIComponent(
      lectureId
    )}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    let message =
      `Failed to fetch chat sessions (${response.status})`;

    try {
      const data = await response.json();

      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

  return response.json();
}
export async function deleteLecture(
  lectureId: string
) {
  const token = await getAccessToken();

  const response = await fetch(
    `${API_URL}/lectures/${lectureId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    let message =
      `Failed to delete lecture (${response.status})`;

    try {
      const data = await response.json();

      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

  return response.json();
}