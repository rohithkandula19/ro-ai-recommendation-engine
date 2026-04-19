import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { RouteProgress } from "@/components/ui/RouteProgress";
import { ChatWidget } from "@/components/chat/ChatWidget";

export const metadata: Metadata = {
  title: "RO AI Recommendation Engine",
  description: "Netflix-style AI recommendations",
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
            <main>{children}</main>
          </ErrorBoundary>
          <ChatWidget />
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
