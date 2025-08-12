"""
Production Hardening Module
Provides rate limiting, structured logging, monitoring, security, and background warming
"""

import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import prometheus_client as prom
from prometheus_client import Counter, Histogram, Gauge
import json
import hashlib
import os
from contextlib import asynccontextmanager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
AI_REQUEST_COUNT = Counter('ai_requests_total', 'Total AI requests', ['status'])
AI_REQUEST_DURATION = Histogram('ai_request_duration_seconds', 'AI request duration')
CACHE_HIT_COUNT = Counter('cache_hits_total', 'Total cache hits')
CACHE_MISS_COUNT = Counter('cache_misses_total', 'Total cache misses')
ACTIVE_REQUESTS = Gauge('active_requests', 'Number of active requests')
SYSTEM_MEMORY = Gauge('system_memory_bytes', 'System memory usage')
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage')

class RateLimiter:
    """Advanced rate limiter with sliding window and per-user limits"""
    
    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)
        self.requests = defaultdict(lambda: deque())
        self.max_requests = 100  # requests per window
        self.window_size = 60  # seconds
        self.max_concurrent = 10  # concurrent requests per user
        
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests outside window
        while client_requests and now - client_requests[0] > self.window_size:
            client_requests.popleft()
        
        # Check rate limit
        if len(client_requests) >= self.max_requests:
            return False
            
        # Add current request
        client_requests.append(now)
        return True
    
    def get_limiter(self):
        return self.limiter

class SecurityManager:
    """Security manager for input validation and threat detection"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'<script>', r'javascript:', r'data:text/html',
            r'../', r'\.\./', r'%2e%2e',  # Path traversal
            r'UNION.*SELECT', r'DROP.*TABLE',  # SQL injection
            r'exec\(', r'eval\(',  # Code injection
        ]
        self.max_input_length = 1000
        self.blocked_ips = set()
        
    def validate_input(self, text: str) -> tuple[bool, str]:
        """Validate input for security threats"""
        if not text or len(text) > self.max_input_length:
            return False, "Input too long or empty"
            
        # Check for suspicious patterns
        import re
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"Suspicious pattern detected: {pattern}"
                
        return True, "OK"
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input for safe processing"""
        import html
        return html.escape(text.strip())

class BackgroundWarmer:
    """Background service to keep instance warm and pre-warm cache"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.warmup_interval = 300  # 5 minutes
        self.popular_queries = [
            "cars", "food", "sports", "travel", "fashion",
            "technology", "health", "finance", "entertainment"
        ]
        self.running = False
        self.thread = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    def start(self):
        """Start background warming"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._warmup_loop, daemon=True)
            self.thread.start()
            logger.info("Background warmer started")
    
    def stop(self):
        """Stop background warming"""
        self.running = False
        if self.thread:
            self.thread.join()
            logger.info("Background warmer stopped")
    
    def _warmup_loop(self):
        """Main warming loop"""
        while self.running:
            try:
                # Health check
                self._health_check()
                
                # Pre-warm popular queries
                self._pre_warm_cache()
                
                # Wait for next interval
                time.sleep(self.warmup_interval)
                
            except Exception as e:
                logger.error("Background warmer error", error=str(e))
                time.sleep(60)  # Wait 1 minute on error
    
    def _health_check(self):
        """Perform health check to keep instance alive with retry logic"""
        for attempt in range(self.max_retries):
            try:
                import requests
                response = requests.get(f"{self.base_url}/health", timeout=10)
                if response.status_code == 200:
                    logger.info("Health check successful")
                    return True
                else:
                    logger.warning("Health check failed", status=response.status_code, attempt=attempt + 1)
            except Exception as e:
                logger.error("Health check error", error=str(e), attempt=attempt + 1)
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Retrying health check in {wait_time} seconds")
                time.sleep(wait_time)
        
        logger.error("Health check failed after all retries")
        return False
    
    def _pre_warm_cache(self):
        """Pre-warm cache with popular queries and retry logic"""
        for query in self.popular_queries:
            success = False
            for attempt in range(self.max_retries):
                try:
                    import requests
                    url = f"{self.base_url}/api/signals?spec={query}&max_results=5"
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        logger.info("Pre-warmed cache", query=query)
                        success = True
                        break
                    else:
                        logger.warning("Pre-warm failed", query=query, status=response.status_code, attempt=attempt + 1)
                except Exception as e:
                    logger.error("Pre-warm error", query=query, error=str(e), attempt=attempt + 1)
                
                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying pre-warm for {query} in {wait_time} seconds")
                    time.sleep(wait_time)
            
            if not success:
                logger.error("Pre-warm failed after all retries", query=query)

class RequestQueue:
    """Request queue for handling traffic spikes"""
    
    def __init__(self, max_queue_size: int = 100):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing = False
        self.max_workers = 5
        
    async def add_request(self, request_data: Dict) -> str:
        """Add request to queue and return request ID"""
        request_id = hashlib.md5(f"{time.time()}{json.dumps(request_data)}".encode()).hexdigest()[:8]
        
        try:
            await asyncio.wait_for(self.queue.put({
                'id': request_id,
                'data': request_data,
                'timestamp': time.time()
            }), timeout=1.0)
            logger.info("Request queued", request_id=request_id)
            return request_id
        except asyncio.TimeoutError:
            logger.warning("Queue full, request rejected", request_id=request_id)
            raise Exception("Service temporarily overloaded")
    
    async def get_request(self) -> Optional[Dict]:
        """Get next request from queue"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            # Update Prometheus metrics
            SYSTEM_MEMORY.set(memory.used)
            SYSTEM_CPU.set(cpu)
            
            return {
                'uptime': time.time() - self.start_time,
                'memory_used_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'cpu_percent': cpu,
                'request_count': self.request_count,
                'error_count': self.error_count,
                'error_rate': self.error_count / max(self.request_count, 1) * 100
            }
        except ImportError:
            return {
                'uptime': time.time() - self.start_time,
                'error': 'psutil not available'
            }
    
    def increment_request(self):
        """Increment request counter"""
        self.request_count += 1
    
    def increment_error(self):
        """Increment error counter"""
        self.error_count += 1

# Global instances
rate_limiter = RateLimiter()
security_manager = SecurityManager()
request_queue = RequestQueue()
system_monitor = SystemMonitor()
background_warmer = None  # Will be initialized with base URL

def initialize_production_hardening(base_url: str):
    """Initialize all production hardening components"""
    global background_warmer
    
    # Start background warmer
    background_warmer = BackgroundWarmer(base_url)
    background_warmer.start()
    
    # Start Prometheus metrics server
    try:
        prom.start_http_server(8001)
        logger.info("Prometheus metrics server started on port 8001")
    except Exception as e:
        logger.warning("Could not start Prometheus server", error=str(e))
    
    logger.info("Production hardening initialized")

def cleanup_production_hardening():
    """Cleanup production hardening components"""
    if background_warmer:
        background_warmer.stop()
    logger.info("Production hardening cleaned up")

@asynccontextmanager
async def request_context(request_id: str, endpoint: str, method: str):
    """Context manager for request tracking and monitoring"""
    start_time = time.time()
    system_monitor.increment_request()
    ACTIVE_REQUESTS.inc()
    
    try:
        yield
        # Success
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status='200').inc()
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        logger.info("Request completed", 
                   request_id=request_id, 
                   endpoint=endpoint, 
                   method=method, 
                   duration=duration)
    except Exception as e:
        # Error
        system_monitor.increment_error()
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status='500').inc()
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        logger.error("Request failed", 
                    request_id=request_id, 
                    endpoint=endpoint, 
                    method=method, 
                    duration=duration, 
                    error=str(e))
        raise
    finally:
        ACTIVE_REQUESTS.dec()
