from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class BehaviorState(IntEnum):
    UNSEEN = -1
    PASSERBY = 0
    EXPOSED = 1
    SLOWED = 2
    STOPPED = 3
    ENTERED = 4


@dataclass
class TrackStateMachine:
    state: BehaviorState = BehaviorState.UNSEEN

    def mark_passerby(self) -> None:
        self._advance(BehaviorState.PASSERBY)

    def mark_exposed(self) -> None:
        self._advance(BehaviorState.EXPOSED)

    def mark_slowed(self) -> None:
        self._advance(BehaviorState.SLOWED)

    def mark_stopped(self) -> None:
        self._advance(BehaviorState.STOPPED)

    def mark_entered(self) -> None:
        self._advance(BehaviorState.ENTERED)

    def _advance(self, next_state: BehaviorState) -> None:
        if self.state is BehaviorState.ENTERED:
            return
        if next_state > self.state:
            self.state = next_state
