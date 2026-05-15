from __future__ import annotations

import itertools
import random
from typing import Literal

RotationMode = Literal["round_robin", "random"]


class ProxyPool:
    def __init__(self, proxies: list[str], *, rotation: RotationMode = "round_robin") -> None:
        if not proxies:
            raise ValueError("ProxyPool requires at least one proxy URL")
        self._proxies = proxies
        self._rotation = rotation
        self._cycle = itertools.cycle(proxies)

    def __len__(self) -> int:
        return len(self._proxies)

    def next(self) -> str:
        if self._rotation == "random":
            return random.choice(self._proxies)
        return next(self._cycle)


async def proxy_pool_from_apify(proxy_configuration: object, *, pool_size: int = 20) -> ProxyPool:
    urls: list[str] = []
    for _ in range(max(1, pool_size)):
        urls.append(await proxy_configuration.new_url())  # type: ignore[union-attr]
    return ProxyPool(urls)
