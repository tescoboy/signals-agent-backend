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

def keep_alive(base_url: str, interval: int = 300):
    """
    Keep the Render instance alive by pinging the health endpoint.
    
    Args:
        base_url: The base URL of your Render app
        interval: Ping interval in seconds (default: 5 minutes)
    """
    print(f"Starting keep-alive for {base_url}")
    print(f"Ping interval: {interval} seconds")
    
    while True:
        try:
            # Try health endpoint first
            response = requests.get(f"{base_url}/api/monitoring/health", timeout=10)
            if response.status_code == 200:
                print(f"[{datetime.now()}] Health check: ✅ OK")
            else:
                print(f"[{datetime.now()}] Health check: ⚠️ Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Health check: ❌ Failed - {e}")
            
            # Try basic health endpoint as fallback
            try:
                response = requests.get(f"{base_url}/health", timeout=10)
                if response.status_code == 200:
                    print(f"[{datetime.now()}] Basic health check: ✅ OK")
                else:
                    print(f"[{datetime.now()}] Basic health check: ⚠️ Status {response.status_code}")
            except requests.exceptions.RequestException as e2:
                print(f"[{datetime.now()}] Basic health check: ❌ Failed - {e2}")
        
        # Wait for next interval
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
    
    print(f"Keep-alive script starting...")
    print(f"URL: {base_url}")
    print(f"Interval: {interval} seconds")
    print("Press Ctrl+C to stop")
    
    try:
        keep_alive(base_url, interval)
    except KeyboardInterrupt:
        print("\nKeep-alive script stopped by user")
    except Exception as e:
        print(f"Keep-alive script error: {e}")
        sys.exit(1)
