"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { RotatingHero as HeroSection } from "@/components/home/RotatingHero";
import { ContentRow } from "@/components/home/ContentRow";
import { CollectionRow } from "@/components/home/CollectionRow";
import { ServiceFilterBar } from "@/components/home/ServiceFilterBar";
import { useAuth } from "@/hooks/useAuth";

function readPersistedUser(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const raw = window.localStorage.getItem("ro-auth-store");
    if (!raw) return false;
    return !!JSON.parse(raw)?.state?.user;
  } catch {
    return false;
  }
}

export default function BrowsePage() {
  const { user, hydrated, fetchMe } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && !user) fetchMe();
  }, [hydrated, user, fetchMe]);

  useEffect(() => {
    if (hydrated && !user) {
      const t = setTimeout(() => {
        if (!readPersistedUser()) router.replace("/login");
      }, 300);
      return () => clearTimeout(t);
    }
  }, [hydrated, user, router]);

  return (
    <div>
      <HeroSection />
      <ServiceFilterBar />
      <div className="space-y-4 pb-12">
        <ContentRow surface="continue_watching" label="Continue Watching" />
        <ContentRow surface="home" label="Recommended For You" />
        <CollectionRow slug="top-10" label="Top 10 Right Now" />
        <ContentRow surface="trending" label="Trending Now" />
        <CollectionRow slug="dark-and-tense" label="Dark & Tense" />
        <CollectionRow slug="light-and-funny" label="Light & Funny" />
        <ContentRow surface="because_you_watched" label="Because You Watched" />
        <CollectionRow slug="hidden-gems" label="Hidden Gems" />
        <CollectionRow slug="mind-benders" label="Mind-Benders" />
        <CollectionRow slug="short-and-sweet" label="Under 90 Minutes" />
        <CollectionRow slug="marathon-worthy" label="Marathon-Worthy" />
        <ContentRow surface="new_releases" label="New Releases" />
      </div>
    </div>
  );
}
