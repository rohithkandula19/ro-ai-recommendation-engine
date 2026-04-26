import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { PageTransition } from "@/components/layout/PageTransition";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { RouteProgress } from "@/components/ui/RouteProgress";
import { ChatWidget } from "@/components/chat/ChatWidget";

export const metadata: Metadata = {
  title: "RO RecEngine",
  description: "AI-native recommendation engine across every streaming service",
  manifest: "/manifest.json",
  themeColor: "#E50914",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <Providers>
          <RouteProgress />
          <Navbar />
          <ErrorBoundary>
            <main><PageTransition>{children}</PageTransition></main>
          </ErrorBoundary>
          <ChatWidget />
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
