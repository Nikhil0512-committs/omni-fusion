import type { Metadata } from "next";
import "./globals.css";

import { AuthProvider } from "@/components/auth/AuthProvider";

export const metadata: Metadata = {
  title: "Omni-Fusion Healthcare",
  description: "Multimodal AI Cardiovascular Diagnostic Platform",
  manifest: "/manifest.json",
  themeColor: "#0f172a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
