"""Test doubles: a fake transport, clock and sleep. Nothing here touches the network."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import requests

from commonswire.http import Pacer, PoliteClient, RawResponse, UsageLog


@dataclass
class FakeClock:
    now: float = 1_000_000.0
    sleeps: list[float] = field(default_factory=list)

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@dataclass
class FakeTransport:
    """Answers from a table of URL -> list of answers (the last one repeats).

    An answer is a RawResponse, an exception instance, or a (status, body) or
    (status, body, headers) tuple. Unknown URLs answer 404.
    """

    routes: dict[str, list[object]] = field(default_factory=dict)
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def add(self, url: str, *answers: object) -> FakeTransport:
        self.routes.setdefault(url, []).extend(answers)
        return self

    def __call__(
        self, url: str, headers: Mapping[str, str], timeout: float, max_bytes: int
    ) -> RawResponse:
        self.calls.append((url, dict(headers)))
        answers = self.routes.get(url)
        if not answers:
            return RawResponse(url=url, status=404, headers={}, body=b"not found")
        answer = answers.pop(0) if len(answers) > 1 else answers[0]
        if isinstance(answer, BaseException):
            raise answer
        if isinstance(answer, RawResponse):
            return answer
        status, body, *rest = answer  # type: ignore[misc]
        hdrs = rest[0] if rest else {}
        if isinstance(body, str):
            body = body.encode("utf-8")
        truncated = len(body) > max_bytes
        return RawResponse(
            url=url, status=status, headers=hdrs, body=body[:max_bytes], truncated=truncated
        )


def make_test_client(
    tmp_path, transport: FakeTransport, **kwargs
) -> tuple[PoliteClient, FakeClock]:
    clock = FakeClock()
    pacer = Pacer(tmp_path / "interim" / "http.lock", clock=clock.time, sleep=clock.sleep)
    client = PoliteClient(
        usage_log=UsageLog(tmp_path / "usage_log.csv"),
        pacer=pacer,
        transport=transport,
        sleep=clock.sleep,
        jitter=lambda: 0.0,
        **kwargs,
    )
    return client, clock


CONNECTION_ERROR = requests.ConnectionError("connection refused")
