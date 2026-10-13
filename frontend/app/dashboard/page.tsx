"use client";

import {
  ChangeEvent,
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  getLectures,
  uploadLecture,
  deleteLecture,
} from "@/lib/api";

type Lecture = {
  id: string;
  title: string;
  status: string;
  duration_seconds: number | null;
  error_message: string | null;
  created_at: string;
};

const PROCESSING_STATUSES = [
  "uploaded",
  "processing",
  "transcribing",
  "embedding",
];

export default function DashboardPage() {
  const [lectures, setLectures] = useState<Lecture[]>([]);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [title, setTitle] = useState("");

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const [error, setError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");

  async function loadLectures() {
    try {
      const data = await getLectures();

      setLectures(data.lectures || []);
      setError("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load lectures"
      );
    } finally {
      setLoading(false);
    }
  }

  // Initial lecture load
  useEffect(() => {
    loadLectures();
  }, []);

  // Automatically refresh lectures while processing
  useEffect(() => {
    const hasProcessingLectures = lectures.some((lecture) =>
      PROCESSING_STATUSES.includes(lecture.status)
    );

    if (!hasProcessingLectures) {
      return;
    }

    const interval = setInterval(() => {
      loadLectures();
    }, 3000);

    return () => {
      clearInterval(interval);
    };
  }, [lectures]);

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0] || null;

    setSelectedFile(file);

    if (file && !title) {
      const filenameWithoutExtension =
        file.name.replace(/\.[^/.]+$/, "");

      setTitle(filenameWithoutExtension);
    }
  }

  async function handleUpload(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setUploadMessage("");

    if (!selectedFile) {
      setError("Please select a video file.");
      return;
    }

    if (!title.trim()) {
      setError("Please enter a lecture title.");
      return;
    }

    setUploading(true);

    try {
      const result = await uploadLecture(
        selectedFile,
        title.trim()
      );

      setUploadMessage(
        `Lecture uploaded successfully. ID: ${result.lecture_id}`
      );

      setSelectedFile(null);
      setTitle("");

      const fileInput = document.getElementById(
        "lecture-file"
      ) as HTMLInputElement | null;

      if (fileInput) {
        fileInput.value = "";
      }

      await loadLectures();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to upload lecture"
      );
    } finally {
      setUploading(false);
    }
  }
  async function handleDeleteLecture(
    lectureId: string
  ) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this lecture?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await deleteLecture(lectureId);

      await loadLectures();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to delete lecture"
      );
    }
  }
  function formatDuration(
    duration: number | null
  ) {
    if (duration === null) {
      return null;
    }

    const totalSeconds = Math.round(duration);

    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    if (minutes === 0) {
      return `${seconds}s`;
    }

    return `${minutes}m ${seconds}s`;
  }

  function getStatusStyle(status: string) {
  switch (status) {
    case "uploaded":
      return {
        label: "Uploaded",
        className: "bg-gray-100 text-gray-700",
      };

    case "processing":
      return {
        label: "Processing",
        className: "bg-blue-100 text-blue-700",
      };

    case "transcribing":
      return {
        label: "Transcribing",
        className: "bg-blue-100 text-blue-700",
      };

    case "embedding":
      return {
        label: "Creating embeddings",
        className: "bg-blue-100 text-blue-700",
      };

    case "ready":
      return {
        label: "Ready",
        className: "bg-green-100 text-green-700",
      };

    case "failed":
      return {
        label: "Failed",
        className: "bg-red-100 text-red-700",
      };

    default:
      return {
        label: status,
        className: "bg-gray-100 text-gray-700",
      };
  }
  }

  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="mx-auto max-w-5xl">

        {/* Header */}

        <div>
          <h1 className="text-3xl font-bold">
            AI Teaching Assistant
          </h1>

          <p className="mt-2 text-gray-600">
            Upload lectures and ask questions using your
            personal knowledge base.
          </p>
        </div>

        {/* Upload Lecture */}

        <div className="mt-8 rounded-xl bg-white p-6 shadow">

          <h2 className="text-xl font-semibold">
            Upload Lecture
          </h2>

          <form
            onSubmit={handleUpload}
            className="mt-5 space-y-4"
          >

            {/* File */}

            <div>
              <label
                htmlFor="lecture-file"
                className="mb-2 block text-sm font-medium"
              >
                Video file
              </label>

              <input
                id="lecture-file"
                type="file"
                accept=".mp4,.mkv,.avi,.mov,.webm"
                onChange={handleFileChange}
                disabled={uploading}
                className="block w-full rounded-lg border p-2"
              />
            </div>

            {/* Title */}

            <div>
              <label
                htmlFor="lecture-title"
                className="mb-2 block text-sm font-medium"
              >
                Lecture title
              </label>

              <input
                id="lecture-title"
                type="text"
                value={title}
                onChange={(event) =>
                  setTitle(event.target.value)
                }
                disabled={uploading}
                placeholder="Enter lecture title"
                className="w-full rounded-lg border px-3 py-2 outline-none focus:ring-2"
              />
            </div>

            {/* Selected file */}

            {selectedFile && (
              <p className="text-sm text-gray-500">
                Selected: {selectedFile.name}
              </p>
            )}

            {/* Error */}

            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Success */}

            {uploadMessage && (
              <div className="rounded-lg bg-green-50 p-3 text-sm text-green-600">
                {uploadMessage}
              </div>
            )}

            {/* Upload button */}

            <button
              type="submit"
              disabled={uploading}
              className="rounded-lg bg-black px-5 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading
                ? "Uploading..."
                : "Upload Lecture"}
            </button>

          </form>
        </div>

        {/* Lectures */}

        <div className="mt-8 rounded-xl bg-white p-6 shadow">

          <div className="flex items-center justify-between">

            <h2 className="text-xl font-semibold">
              My Lectures
            </h2>

            {lectures.some((lecture) =>
              PROCESSING_STATUSES.includes(
                lecture.status
              )
            ) && (
              <span className="text-sm text-gray-500">
                Updating...
              </span>
            )}

          </div>

          {/* Loading */}

          {loading && (
            <p className="mt-4 text-gray-500">
              Loading lectures...
            </p>
          )}

          {/* Empty */}

          {!loading && lectures.length === 0 && (
            <p className="mt-4 text-gray-500">
              You haven't uploaded any lectures yet.
            </p>
          )}

          {/* Lecture list */}

          {!loading && lectures.length > 0 && (
            <div className="mt-4 space-y-3">

              {lectures.map((lecture) => (

                <div
                  key={lecture.id}
                  className="rounded-lg border p-4"
                >

                  <div className="flex items-center justify-between">

                    <h3 className="font-medium">
                      {lecture.title}
                    </h3>

                    <span
                      className={`rounded-full px-3 py-1 text-sm ${getStatusStyle(lecture.status).className}`}
                    >
                      {getStatusStyle(lecture.status).label}
                    </span>

                  </div>

                  {/* Processing message */}

                  {PROCESSING_STATUSES.includes(
                    lecture.status
                  ) && (
                    <p className="mt-2 text-sm text-gray-500">
                      Your lecture is being processed.
                      This may take some time.
                    </p>
                  )}

                  {/* Duration */}

                  {lecture.duration_seconds !== null && (
                    <p className="mt-2 text-sm text-gray-500">
                      Duration:{" "}
                      {formatDuration(
                        lecture.duration_seconds
                      )}
                    </p>
                  )}

                  {/* Ready */}

                  {lecture.status === "ready" && (
                  <>
                    <p className="mt-2 text-sm text-green-600">
                      Lecture is ready for questions.
                    </p>

                    <div className="mt-3 flex gap-2">
                      <a
                        href={`/chat/${lecture.id}`}
                        className="rounded-lg bg-black px-4 py-2 text-sm text-white"
                      >
                        Open Chat
                      </a>

                      <button
                        type="button"
                        onClick={() =>
                          handleDeleteLecture(lecture.id)
                        }
                        className="rounded-lg border border-red-300 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}

                  {/* Failed */}

                  {lecture.status === "failed" &&
                    lecture.error_message && (
                      <p className="mt-2 text-sm text-red-600">
                        Error:{" "}
                        {lecture.error_message}
                      </p>
                    )}

                  {/* Lecture ID */}

                  <p className="mt-2 text-xs text-gray-400">
                    ID: {lecture.id}
                  </p>

                </div>

              ))}

            </div>
          )}

        </div>

      </div>
    </main>
  );
}