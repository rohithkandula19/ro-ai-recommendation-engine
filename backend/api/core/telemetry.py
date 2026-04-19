"""OpenTelemetry wiring — no-op unless OTEL_EXPORTER_OTLP_ENDPOINT is set.

Call init_telemetry(app) from main.py after app is created.
"""
import os

from loguru import logger


def init_telemetry(app) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("OTEL disabled (no endpoint)")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        resource = Resource.create({SERVICE_NAME: "ro-api"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument()
        logger.info(f"OTEL enabled → {endpoint}")
    except Exception as e:
        logger.warning(f"OTEL init skipped: {e}")


def init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.2,
                        integrations=[FastApiIntegration(), SqlalchemyIntegration()])
        logger.info("Sentry enabled")
    except Exception as e:
        logger.warning(f"Sentry init skipped: {e}")
