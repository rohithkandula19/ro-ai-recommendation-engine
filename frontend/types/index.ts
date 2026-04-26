export type ContentType = "movie" | "series" | "short";

export interface ContentItem {
  id: string;
  title: string;
  type: ContentType;
  thumbnail_url: string | null;
  match_score: number;
  reason_text: string;
  genre_ids: number[];
}

export interface Content {
  id: string;
  title: string;
  type: ContentType;
  genre_ids: number[];
  release_year: number | null;
  duration_seconds: number | null;
  language: string | null;
  maturity_rating: string | null;
  description: string | null;
  thumbnail_url: string | null;
  trailer_url: string | null;
  backdrop_url: string | null;
  youtube_trailer_id: string | null;
  cast_names: string[];
  director: string | null;
  popularity_score: number;
  is_active: boolean;
  created_at: string;
}

export interface RecommendationSurface {
  surface: string;
  items: ContentItem[];
  generated_at: string;
  model_version: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
  subscription_tier: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface Preferences {
  genre_ids: number[];
  preferred_language: string;
  maturity_rating: string;
  onboarding_complete: boolean;
  updated_at: string;
}

export interface Genre {
  id: number;
  name: string;
  slug: string;
}

export interface SearchResult {
  id: string;
  title: string;
  type: ContentType;
  relevance_score: number;
  thumbnail_url: string | null;
}

export type EventType =
  | "click" | "play" | "pause" | "progress" | "complete"
  | "like" | "dislike" | "search" | "add_to_list" | "rate" | "skip"
  | "watch_intent" | "provider_click";

export interface TrackedEvent {
  user_id: string;
  content_id?: string | null;
  event_type: EventType;
  value?: number | null;
  session_id?: string | null;
  device_type?: string | null;
  timestamp?: string;
}
