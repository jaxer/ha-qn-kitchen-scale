"""Turn the raw 5 Hz stream into discrete measurements.

A *measurement* is a stable reading that stayed the same for a few frames and
differs from the previous measurement. Putting a bowl on the scale, then
adding flour, then adding sugar yields three measurements, each with the
difference to the previous one, so the log reads like a recipe.

This module is pure: the caller passes the time in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .const import (
    DEFAULT_HISTORY_SIZE,
    DEFAULT_MIN_DELTA_G,
    DEFAULT_MIN_WEIGHT_G,
    DEFAULT_STABLE_FRAMES,
)
from .protocol import Frame


@dataclass(frozen=True, slots=True)
class Measurement:
    """One stable reading worth remembering."""

    at: datetime
    weight_g: float
    delta_g: float | None
    session: int

    def as_dict(self) -> dict[str, Any]:
        """Serialise for storage and entity attributes."""
        return {
            "at": self.at.isoformat(),
            "weight_g": self.weight_g,
            "delta_g": self.delta_g,
            "session": self.session,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Measurement:
        """Inverse of :meth:`as_dict`."""
        return cls(
            at=datetime.fromisoformat(data["at"]),
            weight_g=float(data["weight_g"]),
            delta_g=None if data.get("delta_g") is None else float(data["delta_g"]),
            session=int(data.get("session", 0)),
        )


@dataclass
class MeasurementLog:
    """Measurement detector plus the bounded history it produces.

    ``measurements`` is newest first.
    """

    stable_frames: int = DEFAULT_STABLE_FRAMES
    min_weight_g: float = DEFAULT_MIN_WEIGHT_G
    min_delta_g: float = DEFAULT_MIN_DELTA_G
    history_size: int = DEFAULT_HISTORY_SIZE
    measurements: list[Measurement] = field(default_factory=list)
    session: int = 0

    _streak_weight: float | None = field(default=None, repr=False)
    _streak: int = field(default=0, repr=False)
    _last_recorded_g: float | None = field(default=None, repr=False)
    _recorded_this_streak: bool = field(default=False, repr=False)

    def start_session(self) -> None:
        """Start a new session: the scale was switched on or reconnected, deltas start over."""
        self.session += 1
        self._last_recorded_g = None
        self._reset_streak()

    def feed(self, frame: Frame, now: datetime) -> Measurement | None:
        """Consume one frame; return the measurement it completed, if any."""
        if not frame.stable:
            self._reset_streak()
            return None

        if self._streak_weight is not None and abs(frame.weight_g - self._streak_weight) < 0.05:
            self._streak += 1
        else:
            self._streak_weight = frame.weight_g
            self._streak = 1
            self._recorded_this_streak = False

        if self._streak < self.stable_frames or self._recorded_this_streak:
            return None
        self._recorded_this_streak = True

        if frame.weight_g < self.min_weight_g:
            # Empty scale: the next load is a fresh item.
            self._last_recorded_g = None
            return None

        previous = self._last_recorded_g
        if previous is not None and abs(frame.weight_g - previous) < self.min_delta_g:
            return None

        measurement = Measurement(
            at=now,
            weight_g=frame.weight_g,
            delta_g=None if previous is None else round(frame.weight_g - previous, 1),
            session=self.session,
        )
        self._last_recorded_g = frame.weight_g
        self.measurements.insert(0, measurement)
        del self.measurements[self.history_size :]
        return measurement

    def clear(self) -> None:
        """Forget every measurement."""
        self.measurements.clear()
        self._last_recorded_g = None
        self._reset_streak()

    def _reset_streak(self) -> None:
        self._streak_weight = None
        self._streak = 0
        self._recorded_this_streak = False
