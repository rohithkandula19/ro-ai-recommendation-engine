/**
 * Cloudflare Worker: image proxy + cache for TMDB / TVMaze posters.
 *
 * Why: TMDB rate-limits direct hotlinking; cached edge responses give
 * sub-20ms posters worldwide and mask the origin from abuse.
 *
 * Usage:
 *   https://cdn.ro-rec.com/img/tmdb/w780/abc.jpg
 *   https://cdn.ro-rec.com/img/tvmaze/<full-path>
 */
export default {
  async fetch(req: Request, env: any, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    const m = url.pathname.match(/^\/img\/(tmdb|tvmaze)\/(.+)$/);
    if (!m) return new Response("Not found", { status: 404 });
    const [, origin, rest] = m;
    const upstream =
      origin === "tmdb"
        ? `https://image.tmdb.org/t/p/${rest}`
        : `https://static.tvmaze.com/${rest}`;

    const cache = caches.default;
    const cached = await cache.match(req);
    if (cached) return cached;

    const resp = await fetch(upstream, { cf: { cacheEverything: true, cacheTtl: 86400 } });
    if (resp.ok) {
      const hdrs = new Headers(resp.headers);
      hdrs.set("Cache-Control", "public, max-age=86400, s-maxage=604800");
      hdrs.set("Access-Control-Allow-Origin", "*");
      const cloned = new Response(resp.body, { status: resp.status, headers: hdrs });
      ctx.waitUntil(cache.put(req, cloned.clone()));
      return cloned;
    }
    return resp;
  },
};
