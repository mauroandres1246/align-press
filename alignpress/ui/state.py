from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List


class GlobalState(Enum):
    INIT = auto()
    IDLE = auto()
    RUN_SIM = auto()
    ERROR = auto()


StateListener = Callable[[GlobalState], None]


@dataclass
class StateStore:
    state: GlobalState = GlobalState.INIT
    _listeners: List[StateListener] = field(default_factory=list)

    def subscribe(self, listener: StateListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)
            listener(self.state)

    def unsubscribe(self, listener: StateListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def set_state(self, new_state: GlobalState) -> None:
        if new_state == self.state:
            return
        self.state = new_state
        for listener in list(self._listeners):
            listener(new_state)
