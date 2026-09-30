"""Deterministic Network Observer and HTTP Request/Response Interceptor."""

import time
from typing import Any

from playwright.async_api import Page, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from apps.worker.browser.config import NetworkCapturePolicy
from apps.worker.browser.events import BrowserEventCollector, BrowserEventType
from apps.worker.browser.sanitization import DataSanitizer


class NetworkRecord(BaseModel):
    """Structured, sanitized representation of an observed HTTP interaction."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    url: str
    method: str
    resource_type: str
    status_code: int | None = None
    status_text: str | None = None
    start_time: float
    end_time: float | None = None
    duration_ms: float = 0.0
    request_headers: dict[str, str] = Field(default_factory=dict)
    response_headers: dict[str, str] = Field(default_factory=dict)
    request_body: str | None = None
    response_body: str | None = None
    failure_reason: str | None = None
    step_index: int = 0


class NetworkObserver:
    """Attaches to a Playwright Page, capturing sanitized network metadata."""

    def __init__(
        self,
        policy: NetworkCapturePolicy | None = None,
        event_collector: BrowserEventCollector | None = None,
    ) -> None:
        self.policy = policy or NetworkCapturePolicy()
        self.sanitizer = DataSanitizer(self.policy)
        self.event_collector = event_collector
        self.records: list[NetworkRecord] = []
        self._active_requests: dict[str, dict[str, Any]] = {}
        self.current_step_index: int = 0

    def attach(self, page: Page) -> None:
        """Attach listeners to the Playwright Page."""
        page.on("request", self._handle_request)
        page.on("response", self._handle_response)
        page.on("requestfailed", self._handle_request_failed)

    async def _handle_request(self, request: Request) -> None:
        req_id = str(id(request))
        raw_url = request.url
        clean_url = self.sanitizer.sanitize_url(raw_url)
        clean_headers = self.sanitizer.sanitize_headers(request.headers)

        body_str = None
        if self.policy.capture_bodies:
            try:
                post_data = request.post_data
                if post_data:
                    c_type = request.headers.get("content-type", "")
                    body_str = self.sanitizer.sanitize_body(post_data, c_type)
            except Exception:
                pass

        self._active_requests[req_id] = {
            "request_id": req_id,
            "url": clean_url,
            "method": request.method,
            "resource_type": request.resource_type,
            "start_time": time.perf_counter(),
            "request_headers": clean_headers,
            "request_body": body_str,
            "step_index": self.current_step_index,
        }

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.REQUEST,
                {
                    "url": clean_url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                },
                step_index=self.current_step_index,
            )

    async def _handle_response(self, response: Response) -> None:
        req = response.request
        req_id = str(id(req))
        req_info = self._active_requests.pop(req_id, None)

        now = time.perf_counter()
        clean_url = self.sanitizer.sanitize_url(response.url)
        clean_headers = self.sanitizer.sanitize_headers(response.headers)

        body_str = None
        if self.policy.capture_bodies:
            try:
                c_type = response.headers.get("content-type", "")
                raw_bytes = await response.body()
                body_str = self.sanitizer.sanitize_body(raw_bytes, c_type)
            except Exception:
                pass

        start_time = req_info["start_time"] if req_info else now
        duration = max(0.0, (now - start_time) * 1000.0)

        record = NetworkRecord(
            request_id=req_id,
            url=clean_url,
            method=response.request.method if req else "GET",
            resource_type=response.request.resource_type if req else "other",
            status_code=response.status,
            status_text=response.status_text,
            start_time=start_time,
            end_time=now,
            duration_ms=duration,
            request_headers=req_info["request_headers"] if req_info else {},
            response_headers=clean_headers,
            request_body=req_info.get("request_body") if req_info else None,
            response_body=body_str,
            step_index=req_info["step_index"] if req_info else self.current_step_index,
        )
        self.records.append(record)

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.RESPONSE,
                {
                    "url": clean_url,
                    "status_code": response.status,
                    "duration_ms": duration,
                },
                step_index=record.step_index,
            )

    def _handle_request_failed(self, request: Request) -> None:
        req_id = str(id(request))
        req_info = self._active_requests.pop(req_id, None)
        now = time.perf_counter()
        clean_url = self.sanitizer.sanitize_url(request.url)
        start_time = req_info["start_time"] if req_info else now
        duration = max(0.0, (now - start_time) * 1000.0)

        failure_text = request.failure
        record = NetworkRecord(
            request_id=req_id,
            url=clean_url,
            method=request.method,
            resource_type=request.resource_type,
            status_code=None,
            status_text=None,
            start_time=start_time,
            end_time=now,
            duration_ms=duration,
            request_headers=req_info["request_headers"] if req_info else {},
            failure_reason=failure_text,
            step_index=req_info["step_index"] if req_info else self.current_step_index,
        )
        self.records.append(record)

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.REQUEST_FAILED,
                {
                    "url": clean_url,
                    "failure_reason": failure_text,
                },
                step_index=record.step_index,
            )

    def get_summary(self, step_index: int | None = None) -> dict[str, Any]:
        """Compute network metrics summary for a specific step or entire session."""
        target_records = (
            [r for r in self.records if r.step_index == step_index]
            if step_index is not None
            else self.records
        )

        total_requests = len(target_records)
        failures = sum(
            1 for r in target_records if r.failure_reason or (r.status_code and r.status_code >= 400)
        )
        durations = [r.duration_ms for r in target_records if r.duration_ms > 0]
        avg_latency = (sum(durations) / len(durations)) if durations else 0.0

        return {
            "total_requests": total_requests,
            "failed_requests": failures,
            "avg_latency_ms": round(avg_latency, 2),
        }

    def clear(self) -> None:
        """Reset records."""
        self.records.clear()
        self._active_requests.clear()
