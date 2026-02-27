from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class VisitDeduplicator:
    """基于IP和资源的访问去重器，防止短时间内重复记录"""

    def __init__(self, window_seconds: int = 300):
        """
        Args:
            window_seconds: 时间窗口（秒），默认5分钟
        """
        self.window_seconds = window_seconds
        self._cache: dict[str, float] = {}
        self._lock = Lock()

    def _make_key(self, ip: str | None, resource: str) -> str:
        """生成缓存键"""
        ip_part = ip or "unknown"
        return f"{ip_part}:{resource}"

    def should_record(self, ip: str | None, resource: str) -> bool:
        """
        检查是否应该记录此次访问

        Args:
            ip: 客户端IP
            resource: 资源标识（如 "home" 或 "site:123"）

        Returns:
            True 表示应该记录，False 表示重复访问
        """
        key = self._make_key(ip, resource)
        now = time.time()

        with self._lock:
            # 清理过期记录
            self._cleanup(now)

            # 检查是否在时间窗口内
            last_visit = self._cache.get(key)
            if last_visit and now - last_visit < self.window_seconds:
                return False

            # 记录本次访问
            self._cache[key] = now
            return True

    def _cleanup(self, now: float) -> None:
        """清理过期的缓存记录"""
        expired_keys = [
            key for key, timestamp in self._cache.items() if now - timestamp >= self.window_seconds
        ]
        for key in expired_keys:
            del self._cache[key]


# 全局单例
visit_deduplicator = VisitDeduplicator(window_seconds=300)
