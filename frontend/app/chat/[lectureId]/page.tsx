"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import { useParams } from "next/navigation";

import {
  getChatHistory,
  getChatSessions,
  sendChatMessage,
} from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type Source = {
  lecture_id: string;
  start_time: number;
  end_time: number;
  content: string;
  similarity: number;
};

type ChatSession = {
  id: string;
  lecture_id: string | null;
  created_at: string;
};

export default function ChatPage() {
  const params = useParams();

  const lectureId = params.lectureId as string;

  const [question, setQuestion] = useState("");

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [sources, setSources] =
    useState<Source[]>([]);

  const [sessionId, setSessionId] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [historyLoading, setHistoryLoading] =
    useState(true);

  const [sessions, setSessions] =
  useState<ChatSession[]>([]);

  const [error, setError] =
    useState("");
  
  async function loadChatSession(
      selectedSessionId: string
    ) {
      try {
        setHistoryLoading(true);
        setError("");

        const history =
          await getChatHistory(
            selectedSessionId
          );

        const restoredMessages: Message[] =
          (history.messages || []).map(
            (message: {
              role: "user" | "assistant";
              content: string;
            }) => ({
              role: message.role,
              content: message.content,
            })
          );

        setSessionId(selectedSessionId);
        setMessages(restoredMessages);
        setSources([]);
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Failed to load conversation"
        );
      } finally {
        setHistoryLoading(false);
      }
    }

  useEffect(() => {
  async function initializeChat() {
    try {
      setHistoryLoading(true);
      setError("");

      const data = await getChatSessions(
        lectureId
      );

      const loadedSessions: ChatSession[] =
        data.sessions || [];

      setSessions(loadedSessions);

      if (loadedSessions.length === 0) {
        setSessionId(null);
        setMessages([]);
        return;
      }

      const latestSession =
        loadedSessions[0];

      await loadChatSession(
        latestSession.id
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load conversation"
      );
    } finally {
      setHistoryLoading(false);
    }
  }

  initializeChat();
  }, [lectureId]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const trimmedQuestion =
      question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    setError("");
    setLoading(true);

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: trimmedQuestion,
      },
    ]);

    setQuestion("");

    try {
      const response =
        await sendChatMessage(
          trimmedQuestion,
          lectureId,
          sessionId || undefined
        );

      if (response.session_id) {
        setSessionId(
          response.session_id
        );

        const sessionData =
          await getChatSessions(
            lectureId
          );

        setSessions(
          sessionData.sessions || []
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: response.answer,
        },
      ]);

      setSources(
        response.sources || []
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to send message"
      );
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    setSessionId(null);
    setMessages([]);
    setSources([]);
    setQuestion("");
    setError("");
  }

  function formatTime(seconds: number) {
    const totalSeconds =
      Math.floor(seconds);

    const minutes =
      Math.floor(totalSeconds / 60);

    const remainingSeconds =
      totalSeconds % 60;

    return `${minutes}:${remainingSeconds
      .toString()
      .padStart(2, "0")}`;
  }

  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="mx-auto max-w-5xl">

        {/* Header */}

        <div className="mb-6 flex items-center justify-between">

          <div>
            <h1 className="text-3xl font-bold">
              Lecture Assistant
            </h1>

            <p className="mt-2 text-sm text-gray-500">
              Ask questions about this lecture.
            </p>
          </div>

          

        </div>
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">

  {/* Chat History */}

        <div className="rounded-xl bg-white p-4 shadow">

          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              Chats
            </h2>

            <button
              onClick={handleNewChat}
              className="text-sm text-gray-500 hover:text-black"
            >
              + New
            </button>
          </div>

          <div className="mt-4 space-y-2">

            {sessions.length === 0 && (
              <p className="text-sm text-gray-400">
                No previous chats
              </p>
            )}

            {sessions.map((session, index) => (
              <button
                key={session.id}
                onClick={() =>
                  loadChatSession(session.id)
                }
                className={`w-full rounded-lg p-3 text-left text-sm ${
                  session.id === sessionId
                    ? "bg-black text-white"
                    : "bg-gray-50 hover:bg-gray-100"
                }`}
              >
                <p className="font-medium">
                  Chat {sessions.length - index}
                </p>

                <p
                  className={`mt-1 text-xs ${
                    session.id === sessionId
                      ? "text-gray-300"
                      : "text-gray-500"
                  }`}
                >
                  {new Date(
                    session.created_at
                  ).toLocaleString()}
                </p>
              </button>
            ))}

          </div>

        </div>

        {/* Chat */}

        <div className="rounded-xl bg-white shadow">

          <div className="min-h-[500px] space-y-4 p-6">

            {historyLoading && (
              <div className="flex min-h-[400px] items-center justify-center">
                <p className="text-gray-500">
                  Loading conversation...
                </p>
              </div>
            )}

            {!historyLoading &&
              messages.length === 0 && (
                <div className="flex min-h-[400px] items-center justify-center">

                  <div className="text-center">

                    <h2 className="text-xl font-semibold">
                      Ask your lecture anything
                    </h2>

                    <p className="mt-2 text-gray-500">
                      Questions are answered using
                      the retrieved lecture content.
                    </p>

                  </div>

                </div>
              )}

            {!historyLoading &&
              messages.map(
                (message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-xl px-4 py-3 ${
                        message.role === "user"
                          ? "bg-black text-white"
                          : "bg-gray-100 text-gray-900"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">
                        {message.content}
                      </p>
                    </div>
                  </div>
                )
              )}

            {loading && (
              <div className="flex justify-start">

                <div className="rounded-xl bg-gray-100 px-4 py-3 text-gray-500">
                  Thinking...
                </div>

              </div>
            )}

          </div>

          {/* Error */}

          {error && (
            <div className="mx-6 mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Input */}

          <form
            onSubmit={handleSubmit}
            className="border-t p-4"
          >
            <div className="flex gap-3">

              <input
                type="text"
                value={question}
                onChange={(event) =>
                  setQuestion(
                    event.target.value
                  )
                }
                placeholder="Ask a question about this lecture..."
                disabled={loading}
                className="flex-1 rounded-lg border px-4 py-3 outline-none focus:ring-2"
              />

              <button
                type="submit"
                disabled={
                  loading ||
                  !question.trim()
                }
                className="rounded-lg bg-black px-6 py-3 text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading
                  ? "..."
                  : "Ask"}
              </button>

            </div>
          </form>

        </div>

        {/* Sources */}

        {sources.length > 0 && (
          <div className="mt-6 rounded-xl bg-white p-6 shadow">

            <h2 className="text-xl font-semibold">
              Retrieved Sources
            </h2>

            <div className="mt-4 space-y-4">

              {sources.map(
                (source, index) => (
                  <div
                    key={index}
                    className="rounded-lg border p-4"
                  >

                    <div className="flex items-center justify-between">

                      <span className="font-medium">
                        Source {index + 1}
                      </span>

                      <span className="text-sm text-gray-500">
                        {formatTime(
                          source.start_time
                        )}
                        {" - "}
                        {formatTime(
                          source.end_time
                        )}
                      </span>

                    </div>

                    <p className="mt-3 text-sm leading-6 text-gray-700">
                      {source.content}
                    </p>

                    <p className="mt-2 text-xs text-gray-400">
                      Similarity:{" "}
                      {source.similarity.toFixed(
                        3
                      )}
                    </p>

                  </div>
                )
              )}

            </div>

          </div>
        )}
      </div>
      </div>
    </main>
  );
}