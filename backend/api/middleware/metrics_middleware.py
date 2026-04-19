import time
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


REQUEST_COUNT = Counter(
    "request_count", "Total API requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "API request latency", ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
RECOMMENDATION_CACHE_HITS = Counter(
    "recommendation_cache_hits", "Recommendation cache hits", ["surface"]
)
RECOMMENDATION_LATENCY = Histogram(
    "recommendation_latency_seconds", "Recommendation generation latency", ["surface"]
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path
        REQUEST_COUNT.labels(method=request.method, path=path, status=str(response.status_code)).inc()
        REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)
        return response
