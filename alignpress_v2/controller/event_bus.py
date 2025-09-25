"""Lightweight synchronous event bus for AlignPress v2."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, List


class EventBus:
    """Allow publishers and subscribers to communicate without tight coupling."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable) -> None:
        self._subscribers[topic].append(callback)

    def publish(self, topic: str, payload) -> None:
        for callback in list(self._subscribers.get(topic, [])):
            callback(payload)
