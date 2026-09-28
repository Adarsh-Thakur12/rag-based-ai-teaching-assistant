import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Teaching Assistant",
  description: "RAG-based AI Teaching Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}