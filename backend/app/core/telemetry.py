try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, amount=1):
            pass
        def observe(self, amount):
            pass
        def set(self, val):
            pass

    Counter = Histogram = Gauge = lambda *args, **kwargs: DummyMetric()
    generate_latest = lambda: b"# Prometheus metrics fallback\n"
    CONTENT_TYPE_LATEST = "text/plain"

REQUEST_COUNTER = Counter(
    "guardai_requests_total",
    "Total requests processed by GuardAI",
    ["endpoint", "status"]
)

POLICY_VIOLATION_COUNTER = Counter(
    "guardai_policy_violations_total",
    "Total policy violations blocked or flagged",
    ["policy_id", "action", "severity"]
)

APPROVAL_COUNTER = Counter(
    "guardai_approvals_total",
    "Total approval decisions",
    ["status"]
)

REQUEST_LATENCY = Histogram(
    "guardai_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "guardai_active_requests",
    "Number of active in-flight requests"
)

PROMPT_WARNING_COUNTER = Counter(
    "guardai_prompt_warnings_total",
    "Total prompt security warnings detected",
    ["threat_type"]
)


def init_opentelemetry(app):
    """Setup OpenTelemetry instrumentation if available."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass
