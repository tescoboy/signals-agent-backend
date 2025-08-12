#!/usr/bin/env python3
"""
Keep Alive Script for Render
Prevents cold starts by periodically pinging the health endpoint
"""

import requests
import time
import os
import sys
from datetime import datetime

def keep_alive(base_url: str, interval: int = 300, max_retries: int = 3):
    """
    Keep the Render instance alive by pinging the health endpoint with retry logic.
    
    Args:
        base_url: The base URL of your Render app
        interval: Ping interval in seconds (default: 5 minutes)
        max_retries: Maximum number of retry attempts (default: 3)
    """
    print(f"Starting keep-alive for {base_url}")
    print(f"Ping interval: {interval} seconds")
    print(f"Max retries: {max_retries}")
    
    while True:
        success = False
        
        # Try health endpoint first with retries
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{base_url}/api/monitoring/health", timeout=10)
                if response.status_code == 200:
                    print(f"[{datetime.now()}] Health check: ✅ OK")
                    success = True
                    break
                else:
                    print(f"[{datetime.now()}] Health check: ⚠️ Status {response.status_code} (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                print(f"[{datetime.now()}] Health check: ❌ Failed - {e} (attempt {attempt + 1})")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                print(f"[{datetime.now()}] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # If health endpoint failed, try basic health endpoint as fallback
        if not success:
            print(f"[{datetime.now()}] Trying basic health endpoint as fallback...")
            for attempt in range(max_retries):
                try:
                    response = requests.get(f"{base_url}/health", timeout=10)
                    if response.status_code == 200:
                        print(f"[{datetime.now()}] Basic health check: ✅ OK")
                        success = True
                        break
                    else:
                        print(f"[{datetime.now()}] Basic health check: ⚠️ Status {response.status_code} (attempt {attempt + 1})")
                except requests.exceptions.RequestException as e:
                    print(f"[{datetime.now()}] Basic health check: ❌ Failed - {e} (attempt {attempt + 1})")
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                    print(f"[{datetime.now()}] Retrying basic health check in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        if not success:
            print(f"[{datetime.now()}] ⚠️ All health checks failed after {max_retries} retries each")
        
        # Wait for next interval
        print(f"[{datetime.now()}] Waiting {interval} seconds until next check...")
        time.sleep(interval)

if __name__ == "__main__":
    # Get URL from command line or environment
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = os.environ.get('RENDER_URL', 'https://signals-agent-backend.onrender.com')
    
    # Get interval from command line or environment
    if len(sys.argv) > 2:
        interval = int(sys.argv[2])
    else:
        interval = int(os.environ.get('KEEP_ALIVE_INTERVAL', '300'))
    
    # Get max retries from command line or environment
    if len(sys.argv) > 3:
        max_retries = int(sys.argv[3])
    else:
        max_retries = int(os.environ.get('KEEP_ALIVE_MAX_RETRIES', '3'))
    
    print(f"Keep-alive script starting...")
    print(f"URL: {base_url}")
    print(f"Interval: {interval} seconds")
    print(f"Max retries: {max_retries}")
    print("Press Ctrl+C to stop")
    
    try:
        keep_alive(base_url, interval, max_retries)
    except KeyboardInterrupt:
        print("\nKeep-alive script stopped by user")
    except Exception as e:
        print(f"Keep-alive script error: {e}")
        sys.exit(1)
