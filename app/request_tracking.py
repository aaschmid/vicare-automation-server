import threading
import time
from collections import Counter, defaultdict
from functools import reduce
from typing import Any, TypedDict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API request statistics."""

    def __init__(self, app, request_tracker: "RequestTracker"):
        super().__init__(app)
        self.request_tracker = request_tracker

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/health"):
            message = self._extract_message(response)
            self.request_tracker.record_request(request.url.path, response.status_code, message)
        return response

    @staticmethod
    def _extract_message(response: Response) -> str:
        if response.status_code >= 400:
            # For `PlainTextResponse` used by exception handlers, `body` is directly accessible
            if isinstance(response, PlainTextResponse):
                body = response.body
                if body:
                    return body.decode("utf-8") if isinstance(body, bytes) else str(body)
        return "n/a"


class LastFailureMessage(TypedDict):
    endpoint: str
    message: str
    status_code: int
    timestamp: float


class RequestTracker:
    """Thread-safe request statistics tracker with optimized lock usage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Track counts by endpoint: {endpoint: {status_code: count}}
        self._counts_by_endpoint: dict[str, Counter[int]] = defaultdict(Counter)
        self._last_failure_message: LastFailureMessage | None = None

    def record_request(self, endpoint: str, status_code: int, message: str) -> None:
        """Record a request with its status code, optional message, and endpoint."""
        with self._lock:
            self._counts_by_endpoint[endpoint][status_code] += 1

            if status_code < 200 or status_code >= 300:
                if self._last_failure_message is None or time.time() - self._last_failure_message["timestamp"] > 3600:
                    self._last_failure_message = LastFailureMessage(
                        endpoint=endpoint,
                        message=message,
                        status_code=status_code,
                        timestamp=time.time(),
                    )

    def get_statistics(self) -> dict[str, Any]:
        """Get current request statistics grouped by status code and by endpoint."""
        # Quick conversion inside the lock (minimal time - just dict conversion)
        with self._lock:
            # Convert Counter objects to regular dicts to avoid holding references
            counts_by_endpoint = {endpoint: dict(counter) for endpoint, counter in self._counts_by_endpoint.items()}

        # Calculate overall counts by aggregating endpoint-level counts
        all_counts: Counter[int] = reduce(lambda acc, d: acc + Counter(d), counts_by_endpoint.values(), Counter[int]())

        # Calculate success and failure counts for overall
        success_count = sum(count for status_code, count in all_counts.items() if 200 <= status_code < 300)
        failure_count = sum(
            count for status_code, count in all_counts.items() if status_code < 200 or status_code >= 300
        )

        return {
            "overall": {
                "success": success_count,
                "failure": failure_count,
            },
            "by_status_code": dict(all_counts),
            "by_endpoint": counts_by_endpoint,
        }

    def get_last_failure_message(self) -> LastFailureMessage | None:
        """Get the last failure message.

        Optimized to minimize lock time: quickly copies the failure dict inside the lock.
        """
        with self._lock:
            if self._last_failure_message is None:
                return None
            return LastFailureMessage(**self._last_failure_message)

    def reset(self) -> None:
        """Reset all statistics (mainly for testing)."""
        with self._lock:
            self._counts_by_endpoint.clear()
            self._last_failure_message = None
