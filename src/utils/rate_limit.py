import time
from utils.logger import get_logger

logger = get_logger("rate_limit")

class TokenBucket:
    def __init__(self, rate_per_min: int):
        self.capacity = rate_per_min
        self.tokens = rate_per_min
        self.last = time.time()

    def consume(self, n=1):
        now = time.time()
        elapsed = now - self.last
        refill = elapsed * (self.capacity / 60.0)
        self.tokens = min(self.capacity, self.tokens + refill)
        self.last = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        sleep_for = (n - self.tokens) * (60.0 / self.capacity)
        logger.debug(f"Rate limit sleep: {sleep_for:.2f}s")
        time.sleep(sleep_for)
        self.tokens = 0
        self.last = time.time()
        return True
