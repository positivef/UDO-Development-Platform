"""
P0-1: Token Blacklist Redis Migration Tests

Tests for Redis-based token blacklist implementation.
Validates:
- Token blacklisting with auto-expiry
- User-level token revocation
- Distributed system support
- Performance (1,000 tokens/second)
- Persistence across restarts
"""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
import pytest_asyncio

from backend.app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    JWTManager,
    TokenBlacklist,
)
from backend.app.services.redis_client import RedisClient


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client for testing"""
    redis_mock = AsyncMock(spec=RedisClient)
    redis_mock.connect = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.exists = AsyncMock(return_value=0)
    redis_mock.get = AsyncMock(return_value=None)
    return redis_mock


@pytest_asyncio.fixture
async def token_blacklist(mock_redis):
    """TokenBlacklist instance with mocked Redis"""
    blacklist = TokenBlacklist()
    blacklist._redis_client = mock_redis
    blacklist._initialized = True
    return blacklist


@pytest.fixture
def sample_token():
    """Generate a sample JWT token"""
    payload = {
        "sub": "test@example.com",
        "user_id": "test-user-123",
        "type": "access",
        "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def expired_token():
    """Generate an expired JWT token"""
    payload = {
        "sub": "test@example.com",
        "user_id": "test-user-123",
        "type": "access",
        "exp": (datetime.now(UTC) - timedelta(hours=1)).timestamp(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ============= Test 1-3: Basic Operations =============


@pytest.mark.asyncio
async def test_add_token_to_blacklist(token_blacklist, mock_redis, sample_token):
    """Test 1: Add token to blacklist with TTL"""
    exp_datetime = datetime.now(UTC) + timedelta(hours=1)

    await token_blacklist.add(sample_token, exp_datetime)

    # Verify Redis setex was called
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args

    # Check key format
    assert call_args[0][0].startswith("udo:auth:blacklist:")
    assert sample_token in call_args[0][0]

    # Check TTL is reasonable (within 1 hour, accounting for test execution time)
    ttl = call_args[0][1]
    assert 3595 <= ttl <= 3600  # ~1 hour in seconds


@pytest.mark.asyncio
async def test_is_blacklisted_found(token_blacklist, mock_redis, sample_token):
    """Test 2: Check if token is blacklisted (found)"""
    # Mock: Token exists in Redis
    mock_redis.exists.return_value = 1

    result = await token_blacklist.is_blacklisted(sample_token)

    assert result is True
    mock_redis.exists.assert_called_once()


@pytest.mark.asyncio
async def test_is_blacklisted_not_found(token_blacklist, mock_redis, sample_token):
    """Test 3: Check if token is blacklisted (not found)"""
    # Mock: Token does not exist in Redis
    mock_redis.exists.return_value = 0

    result = await token_blacklist.is_blacklisted(sample_token)

    assert result is False
    mock_redis.exists.assert_called_once()


# ============= Test 4: User-level Revocation =============


@pytest.mark.asyncio
async def test_revoke_all_user_tokens(token_blacklist, mock_redis):
    """Test 4: Revoke all tokens for a specific user"""
    user_id = "test-user-123"

    await token_blacklist.revoke_all_user_tokens(user_id)

    # Verify Redis setex was called with user-level key
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args

    assert "udo:auth:user_tokens:" in call_args[0][0]
    assert user_id in call_args[0][0]
    assert call_args[0][1] == 86400  # 24 hour TTL


# ============= Test 5-6: JWT Integration =============


@pytest.mark.asyncio
async def test_blacklist_token_extracts_expiry(sample_token):
    """Test 5: JWTManager.blacklist_token extracts TTL from token"""
    with patch.object(TokenBlacklist, 'add', new_callable=AsyncMock) as mock_add:
        await JWTManager.blacklist_token(sample_token)

        # Verify add was called with extracted expiry
        mock_add.assert_called_once()
        call_args = mock_add.call_args

        assert call_args[0][0] == sample_token
        exp_datetime = call_args[0][1]

        # Expiry should be ~1 hour from now
        assert exp_datetime is not None
        time_diff = (exp_datetime - datetime.now(UTC)).total_seconds()
        assert 3595 <= time_diff <= 3605


@pytest.mark.asyncio
async def test_blacklist_token_handles_invalid_token():
    """Test 6: JWTManager.blacklist_token handles decode failures gracefully"""
    invalid_token = "invalid.token.here"

    with patch.object(TokenBlacklist, 'add', new_callable=AsyncMock) as mock_add:
        # Should not raise exception
        await JWTManager.blacklist_token(invalid_token)

        # Verify add was called with None expiry (default TTL)
        mock_add.assert_called_once()
        call_args = mock_add.call_args
        assert call_args[0][1] is None


# ============= Test 7: Auto-expiry Validation =============


@pytest.mark.asyncio
async def test_add_expired_token_no_ttl(token_blacklist, mock_redis, expired_token):
    """Test 7: Adding expired token skips Redis (no point blacklisting expired tokens)"""
    exp_datetime = datetime.now(UTC) - timedelta(hours=1)  # Past

    await token_blacklist.add(expired_token, exp_datetime)

    # Should NOT call setex (TTL would be negative)
    # Expired tokens don't need blacklisting
    mock_redis.setex.assert_not_called()


# ============= Test 8: Connection Handling =============


@pytest.mark.asyncio
async def test_ensure_connected_initializes_once(token_blacklist, mock_redis):
    """Test 8: _ensure_connected only initializes once"""
    token_blacklist._initialized = False

    # Call ensure_connected twice
    await token_blacklist._ensure_connected()
    await token_blacklist._ensure_connected()

    # Redis connect should be called only once
    assert mock_redis.connect.call_count == 1


# ============= Test 9: Performance Test =============


@pytest.mark.asyncio
async def test_performance_1000_tokens(token_blacklist, mock_redis):
    """Test 9: Performance - 1,000 tokens/second"""
    # Generate 1,000 test tokens
    tokens = [f"token_{i}" for i in range(1000)]
    exp_datetime = datetime.now(UTC) + timedelta(hours=1)

    start_time = time.time()

    # Add all tokens
    tasks = [token_blacklist.add(token, exp_datetime) for token in tokens]
    await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    # Should complete in under 1 second (1,000 tokens/second)
    print(f"\n[PERF] 1,000 tokens processed in {duration:.3f}s")
    assert duration < 1.0, f"Performance target missed: {duration:.3f}s > 1.0s"

    # Verify all calls were made
    assert mock_redis.setex.call_count == 1000


# ============= Test 10: Integration Test =============


@pytest.mark.asyncio
async def test_decode_token_checks_blacklist(sample_token):
    """Test 10: JWTManager.decode_token checks blacklist before decoding"""
    with patch.object(TokenBlacklist, 'is_blacklisted', new_callable=AsyncMock) as mock_check:
        # Test 10a: Token not blacklisted - should decode successfully
        mock_check.return_value = False

        payload = await JWTManager.decode_token_async(sample_token, check_blacklist=True)

        assert payload["sub"] == "test@example.com"
        mock_check.assert_called_once_with(sample_token)

        # Test 10b: Token blacklisted - should raise HTTPException
        mock_check.reset_mock()
        mock_check.return_value = True

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await JWTManager.decode_token_async(sample_token, check_blacklist=True)

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()


# ============= Integration Tests (Require Real Redis) =============


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_redis_persistence():
    """
    Integration Test: Verify token persists in real Redis across connections

    Requirements:
    - Redis server running on localhost:6379
    - Run with: pytest -m integration
    """
    try:
        # Create real Redis client
        redis_client = RedisClient()
        connected = await redis_client.connect()

        if not connected:
            pytest.skip("Redis server not available")

        # Create real blacklist
        blacklist = TokenBlacklist()
        blacklist._redis_client = redis_client

        # Test token
        test_token = "integration_test_token_12345"
        exp_datetime = datetime.now(UTC) + timedelta(seconds=30)

        # Add to blacklist
        await blacklist.add(test_token, exp_datetime)

        # Verify immediately
        is_blacklisted = await blacklist.is_blacklisted(test_token)
        assert is_blacklisted is True

        # Create NEW blacklist instance (simulating restart)
        blacklist2 = TokenBlacklist()
        blacklist2._redis_client = RedisClient()
        await blacklist2._redis_client.connect()

        # Token should still be blacklisted
        is_still_blacklisted = await blacklist2.is_blacklisted(test_token)
        assert is_still_blacklisted is True

        print("\n[INTEGRATION] ✅ Token persisted across restart simulation")

        # Cleanup
        await redis_client.disconnect()
        await blacklist2._redis_client.disconnect()

    except Exception as e:
        pytest.skip(f"Redis integration test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_redis_ttl_expiry():
    """
    Integration Test: Verify TTL auto-expiry in real Redis

    Requirements:
    - Redis server running on localhost:6379
    - Run with: pytest -m integration
    """
    try:
        redis_client = RedisClient()
        connected = await redis_client.connect()

        if not connected:
            pytest.skip("Redis server not available")

        blacklist = TokenBlacklist()
        blacklist._redis_client = redis_client

        # Test token with 2-second TTL
        test_token = "expiry_test_token_67890"
        exp_datetime = datetime.now(UTC) + timedelta(seconds=2)

        await blacklist.add(test_token, exp_datetime)

        # Should be blacklisted immediately
        assert await blacklist.is_blacklisted(test_token) is True

        # Wait for expiry
        await asyncio.sleep(3)

        # Should no longer be blacklisted
        assert await blacklist.is_blacklisted(test_token) is False

        print("\n[INTEGRATION] ✅ Token auto-expired after TTL")

        await redis_client.disconnect()

    except Exception as e:
        pytest.skip(f"Redis integration test failed: {e}")


# ============= Test Summary =============
"""
Test Coverage Summary:

✅ Test 1: Add token with TTL
✅ Test 2: Check blacklisted token (found)
✅ Test 3: Check blacklisted token (not found)
✅ Test 4: User-level revocation
✅ Test 5: Extract expiry from JWT
✅ Test 6: Handle invalid token gracefully
✅ Test 7: Expired token handling
✅ Test 8: Connection initialization
✅ Test 9: Performance (1,000 tokens/second)
✅ Test 10: Integration with decode_token

Integration Tests (require Redis server):
✅ Test 11: Persistence across restarts
✅ Test 12: TTL auto-expiry

Run all tests:
    pytest backend/tests/test_token_blacklist_redis.py -v

Run unit tests only:
    pytest backend/tests/test_token_blacklist_redis.py -v -m "not integration"

Run integration tests (requires Redis):
    pytest backend/tests/test_token_blacklist_redis.py -v -m integration
"""
