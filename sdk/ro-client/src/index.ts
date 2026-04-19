/**
 * @ro/client — TypeScript SDK for the RO AI Recommendation Engine.
 *
 * Usage:
 *   import { RoClient } from "@ro/client";
 *   const ro = new RoClient({ baseUrl: "https://api.ro-rec.com", apiKey: "xxx" });
 *   const home = await ro.recommendations("home");
 *   const chat = await ro.chat.send("what should I watch tonight?");
 */

export interface RoConfig {
  baseUrl: string;
  apiKey?: string;
  fetch?: typeof fetch;
}

export interface ContentItem {
  id: string;
  title: string;
  type: "movie" | "series" | "short";
  thumbnail_url: string | null;
  match_score: number;
  reason_text: string;
  genre_ids: number[];
}

export interface RecommendationResponse {
  surface: string;
  items: ContentItem[];
  generated_at: string;
  model_version: string;
}

export interface VibeVector {
  pace: number; emotion: number; darkness: number;
  humor: number; complexity: number; spectacle: number;
}

export class RoClient {
  private baseUrl: string;
  private token?: string;
  private f: typeof fetch;

  constructor(cfg: RoConfig) {
    this.baseUrl = cfg.baseUrl.replace(/\/$/, "");
    this.token = cfg.apiKey;
    this.f = cfg.fetch ?? globalThis.fetch.bind(globalThis);
  }

  setToken(token: string) { this.token = token; }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const r = await this.f(this.baseUrl + path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) throw new Error(`RO ${method} ${path} → ${r.status}`);
    return r.json() as Promise<T>;
  }

  // ── Auth ─────────────────────────────────────────────
  async login(email: string, password: string) {
    const r = await this.request<{ access_token: string; refresh_token: string }>("POST", "/auth/login", { email, password });
    this.token = r.access_token;
    return r;
  }

  // ── Recommendations ──────────────────────────────────
  recommendations(surface: "home" | "trending" | "new_releases" | "because_you_watched" | "continue_watching", limit = 20) {
    return this.request<RecommendationResponse>("GET", `/recommendations/${surface}?limit=${limit}`);
  }

  moodRecs(chillTense: number, lightThoughtful: number, limit = 20) {
    return this.request<RecommendationResponse>("POST", "/recommendations/mood",
      { chill_tense: chillTense, light_thoughtful: lightThoughtful, limit });
  }

  batch(surfaces: string[], limit = 20) {
    return this.request<{ surfaces: Record<string, RecommendationResponse> }>("POST", "/recommendations/batch",
      { surfaces, limit });
  }

  // ── User / DNA ───────────────────────────────────────
  tasteDna() {
    return this.request<{ dna: VibeVector; samples: number }>("GET", "/users/me/taste-dna");
  }

  dnaTimeline(days = 90) {
    return this.request<{ points: Array<VibeVector & { date: string; samples: number }> }>("GET", `/users/me/dna-timeline?days=${days}`);
  }

  // ── Chat ─────────────────────────────────────────────
  chat = {
    send: async (message: string, onToken?: (t: string) => void) => {
      const r = await this.f(this.baseUrl + "/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
        },
        body: JSON.stringify({ message }),
      });
      if (!r.ok || !r.body) throw new Error(`chat ${r.status}`);
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        acc += chunk;
        onToken?.(chunk);
      }
      return acc;
    },
    agent: (message: string) => this.request<{ reply: string; actions: Array<{ kind: string; content_id: string; label: string }> }>(
      "POST", "/chat/agent", { message }),
    decisive: (context = "") => this.request<{ id: string; title: string; verdict: string }>(
      "POST", "/chat/decisive", { context }),
    addFact: (fact: string) => this.request("POST", "/chat/facts", { fact }),
    usage: () => this.request<{ tokens_used: number; quota: number }>("GET", "/chat/usage"),
  };

  // ── Search ───────────────────────────────────────────
  search(q: string, limit = 20) {
    return this.request<{ results: any[] }>("GET", `/search?q=${encodeURIComponent(q)}&limit=${limit}`);
  }

  semanticSearch(query: string, limit = 20) {
    return this.request<{ results: ContentItem[] }>("POST", "/search/semantic", { query, limit });
  }

  // ── Queues / Watchlist ───────────────────────────────
  queues = () => this.request<{ items: any[] }>("GET", "/users/me/queues");
  addToQueue = (queueId: string, contentId: string) =>
    this.request("POST", `/users/me/queues/${queueId}/items/${contentId}`);

  // ── Killer features ──────────────────────────────────
  wrapped = (year: number) => this.request("GET", `/wrapped/${year}`);
  blindDateStart = () => this.request<{ blind_date_id: string; hint: string }>("POST", "/blind-date/start");
  mixer = (otherUserId: string, limit = 12) => this.request("POST", "/mixer", { other_user_id: otherUserId, limit });
  achievements = () => this.request<{ items: any[]; progress: string }>("GET", "/achievements");
}

export default RoClient;
