import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for controlling request frequency"""
    
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, deque] = defaultdict(deque)
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def is_allowed(self, user_id: int) -> bool:
        """
        Check if request is allowed for user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if request is allowed, False otherwise
        """
        async with self.locks[user_id]:
            current_time = time.time()
            user_requests = self.requests[user_id]
            
            # Remove old requests outside time window
            while user_requests and current_time - user_requests[0] > self.time_window:
                user_requests.popleft()
            
            # Check if under limit
            if len(user_requests) < self.max_requests:
                user_requests.append(current_time)
                return True
            
            return False
    
    async def wait_if_needed(self, user_id: int) -> Optional[float]:
        """
        Wait if rate limit exceeded
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Wait time in seconds if rate limited, None if allowed
        """
        if await self.is_allowed(user_id):
            return None
        
        # Calculate wait time
        user_requests = self.requests[user_id]
        if user_requests:
            oldest_request = user_requests[0]
            wait_time = self.time_window - (time.time() - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limiting user {user_id} for {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                return wait_time
        
        return None
    
    def get_remaining_requests(self, user_id: int) -> int:
        """
        Get remaining requests for user in current window
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        while user_requests and current_time - user_requests[0] > self.time_window:
            user_requests.popleft()
        
        return max(0, self.max_requests - len(user_requests))
    
    def get_reset_time(self, user_id: int) -> Optional[float]:
        """
        Get time when rate limit resets for user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Unix timestamp when limit resets, None if not rate limited
        """
        user_requests = self.requests[user_id]
        if not user_requests or len(user_requests) < self.max_requests:
            return None
        
        oldest_request = user_requests[0]
        return oldest_request + self.time_window
    
    async def get_cooldown_time(self, user_id: int) -> int:
        """
        Get cooldown time for user in seconds
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Cooldown time in seconds
        """
        user_requests = self.requests[user_id]
        if not user_requests:
            return 0
        
        current_time = time.time()
        oldest_request = user_requests[0]
        cooldown = self.time_window - (current_time - oldest_request)
        return max(0, int(cooldown))
    
    def clear_user(self, user_id: int):
        """
        Clear rate limit data for user
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self.requests:
            del self.requests[user_id]
        if user_id in self.locks:
            del self.locks[user_id]
    
    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics
        
        Returns:
            Dictionary with statistics
        """
        current_time = time.time()
        active_users = 0
        total_requests = 0
        
        for user_id, user_requests in self.requests.items():
            # Remove old requests
            while user_requests and current_time - user_requests[0] > self.time_window:
                user_requests.popleft()
            
            if user_requests:
                active_users += 1
                total_requests += len(user_requests)
        
        return {
            'active_users': active_users,
            'total_requests': total_requests,
            'max_requests_per_window': self.max_requests,
            'time_window': self.time_window
        }

class GlobalRateLimiter:
    """Global rate limiter for all users combined"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialize global rate limiter
        
        Args:
            max_requests: Maximum total requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = asyncio.Lock()
    
    async def is_allowed(self) -> bool:
        """
        Check if request is allowed globally
        
        Returns:
            True if request is allowed, False otherwise
        """
        async with self.lock:
            current_time = time.time()
            
            # Remove old requests
            while self.requests and current_time - self.requests[0] > self.time_window:
                self.requests.popleft()
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(current_time)
                return True
            
            return False
    
    async def wait_if_needed(self) -> Optional[float]:
        """
        Wait if global rate limit exceeded
        
        Returns:
            Wait time in seconds if rate limited, None if allowed
        """
        if await self.is_allowed():
            return None
        
        # Calculate wait time
        if self.requests:
            oldest_request = self.requests[0]
            wait_time = self.time_window - (time.time() - oldest_request)
            if wait_time > 0:
                logger.info(f"Global rate limit exceeded, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                return wait_time
        
        return None
    
    def get_remaining_requests(self) -> int:
        """
        Get remaining requests in current window
        
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        
        # Remove old requests
        while self.requests and current_time - self.requests[0] > self.time_window:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))