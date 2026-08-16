import type { Metadata } from "next";
import "./globals.css";

import { AuthProvider } from "@/components/auth/AuthProvider";

// Force all pages to render dynamically at runtime.
// Supabase client requires NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
// which are only available at runtime, not during static build generation.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Omni-Fusion Healthcare",
  description: "Multimodal AI Cardiovascular Diagnostic Platform",
  manifest: "/manifest.json",
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
