"""Small deterministic interval schedule abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class IntervalSchedule:
    """Run a job repeatedly at a fixed interval."""

    seconds: int

    def __post_init__(self) -> None:
        if self.seconds < 1:
            raise ValueError("seconds must be at least 1")

    def next_after(self, value: datetime) -> datetime:
        """Return the next scheduled time after ``value``."""

        return value + timedelta(seconds=self.seconds)

    @classmethod
    def parse(cls, expression: str) -> "IntervalSchedule":
        """Parse expressions such as ``@every 30s`` or ``@every 5m``."""

        prefix = "@every "
        if not expression.startswith(prefix):
            raise ValueError("schedule must use '@every <number><s|m|h>'")

        raw = expression[len(prefix):].strip()
        if len(raw) < 2:
            raise ValueError("invalid interval schedule")

        unit = raw[-1]
        try:
            amount = int(raw[:-1])
        except ValueError as exc:
            raise ValueError("invalid interval amount") from exc

        multipliers = {"s": 1, "m": 60, "h": 3600}
        if unit not in multipliers:
            raise ValueError("interval unit must be s, m, or h")

        return cls(seconds=amount * multipliers[unit])
