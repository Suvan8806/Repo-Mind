import time
import psutil

class PerformanceTracker:
    def __init__(self):
        self.start_time = None
        self.start_mem = None

    def start(self):
        self.start_time = time.time()
        self.start_mem = psutil.Process().memory_info().rss / (1024 * 1024)

    def stop(self, token_count):
        duration = time.time() - self.start_time
        end_mem = psutil.Process().memory_info().rss / (1024 * 1024)
        tps = token_count / duration if duration > 0 else 0
        return {
            "duration_sec": round(duration, 2),
            "tokens_per_sec": round(tps, 2),
            "memory_used_mb": round(end_mem - self.start_mem, 2)
        }