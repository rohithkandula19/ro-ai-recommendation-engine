import axios, { AxiosError, AxiosInstance } from "axios";
import Cookies from "js-cookie";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ACCESS_COOKIE = "ro_access";
const REFRESH_COOKIE = "ro_refresh";

let inMemoryToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  inMemoryToken = access;
  Cookies.set(ACCESS_COOKIE, access, { sameSite: "lax", secure: false });
  Cookies.set(REFRESH_COOKIE, refresh, { sameSite: "lax", secure: false });
}

export function clearTokens() {
  inMemoryToken = null;
  Cookies.remove(ACCESS_COOKIE);
  Cookies.remove(REFRESH_COOKIE);
}

export function getAccessToken(): string | null {
  return inMemoryToken || Cookies.get(ACCESS_COOKIE) || null;
}

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refresh = Cookies.get(REFRESH_COOKIE);
  if (!refresh) return null;
  try {
    const r = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
    const { access_token, refresh_token } = r.data;
    setTokens(access_token, refresh_token);
    return access_token;
  } catch {
    clearTokens();
    try {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("ro-auth-store");
      }
    } catch {}
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original: any = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      if (!refreshing) refreshing = refreshAccess();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess) {
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api.request(original);
      }
      // Refresh failed — hard kick to login on the next paint
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.replace("/login");
      }
    }
    return Promise.reject(error);
  }
);
