class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay_seconds: float = 1.0,
        multiplier: float = 2.0,
        max_delay_seconds: float = 30.0,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if base_delay_seconds < 0:
            raise ValueError("base_delay_seconds cannot be negative")
        if multiplier < 1:
            raise ValueError("multiplier must be at least 1")
        if max_delay_seconds < 0:
            raise ValueError("max_delay_seconds cannot be negative")

        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.multiplier = multiplier
        self.max_delay_seconds = max_delay_seconds

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.max_attempts

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt < 1:
            raise ValueError("attempt must be at least 1")

        delay = self.base_delay_seconds * (
            self.multiplier ** (attempt - 1)
        )
        return min(delay, self.max_delay_seconds)
