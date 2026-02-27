from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import time


@dataclass
class _ClientRateState:
    attempts: deque[float] = field(default_factory=deque)
    locked_until: float = 0.0


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 60,
        lock_seconds: int = 15 * 60,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self._states: dict[str, _ClientRateState] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._states.clear()

    def reset_client(self, client_ip: str) -> None:
        with self._lock:
            self._states.pop(client_ip, None)

    def check_and_record(self, client_ip: str, now_ts: float | None = None) -> tuple[bool, int]:
        now = now_ts if now_ts is not None else time()
        with self._lock:
            state = self._states.setdefault(client_ip, _ClientRateState())

            if state.locked_until > now:
                retry_after = int(state.locked_until - now)
                return False, max(retry_after, 1)

            window_start = now - self.window_seconds
            while state.attempts and state.attempts[0] <= window_start:
                state.attempts.popleft()

            state.attempts.append(now)
            if len(state.attempts) > self.max_attempts:
                state.attempts.clear()
                state.locked_until = now + self.lock_seconds
                return False, self.lock_seconds

            return True, 0

