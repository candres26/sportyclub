"""Limitador de intentos en memoria (ventana deslizante).

Pensado para el MVP con una sola replica de la API: el estado vive en el proceso,
asi que con varias replicas cada una lleva su propia cuenta. Para escalar
horizontalmente hay que moverlo a Redis u otro almacen compartido.
"""

import time
from collections import deque

from app.core.exceptions import TooManyRequestsError


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits = max_hits
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def _recent(self, key: str) -> deque[float] | None:
        hits = self._hits.get(key)
        if hits is None:
            return None
        cutoff = time.monotonic() - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if not hits:
            del self._hits[key]
            return None
        return hits

    def check(self, key: str) -> None:
        hits = self._recent(key)
        if hits is not None and len(hits) >= self.max_hits:
            raise TooManyRequestsError()

    def hit(self, key: str) -> None:
        self._recent(key)
        self._hits.setdefault(key, deque()).append(time.monotonic())

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)

    def clear(self) -> None:
        self._hits.clear()


# Intentos fallidos de login por cuenta: frena la fuerza bruta contra un correo.
login_failures = SlidingWindowLimiter(max_hits=10, window_seconds=15 * 60)
# Solicitudes de reset por cuenta: evita inundar el buzon de la victima.
password_reset_requests = SlidingWindowLimiter(max_hits=5, window_seconds=60 * 60)
