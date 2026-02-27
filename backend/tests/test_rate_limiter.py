from app.utils.rate_limiter import LoginRateLimiter


def test_rate_limiter_locks_after_exceeding_limit() -> None:
    limiter = LoginRateLimiter(max_attempts=2, window_seconds=60, lock_seconds=900)

    assert limiter.check_and_record("1.1.1.1", now_ts=1) == (True, 0)
    assert limiter.check_and_record("1.1.1.1", now_ts=2) == (True, 0)
    allowed, retry_after = limiter.check_and_record("1.1.1.1", now_ts=3)

    assert allowed is False
    assert retry_after == 900


def test_rate_limiter_unlocks_after_lock_window() -> None:
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60, lock_seconds=10)

    assert limiter.check_and_record("2.2.2.2", now_ts=1) == (True, 0)
    assert limiter.check_and_record("2.2.2.2", now_ts=2) == (False, 10)
    still_locked = limiter.check_and_record("2.2.2.2", now_ts=5)
    unlocked = limiter.check_and_record("2.2.2.2", now_ts=13)

    assert still_locked[0] is False
    assert still_locked[1] > 0
    assert unlocked == (True, 0)

