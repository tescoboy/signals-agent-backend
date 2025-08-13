#!/usr/bin/env python3
"""
Update platform_deployments table with random distribution
Every segment gets at least one platform, some get multiple, some get all
"""

import sqlite3
import random
from datetime import datetime

def update_platform_deployments():
    """Update platform_deployments with random distribution for all segments"""
    
    # Connect to database
    conn = sqlite3.connect('signals_agent.db')
    cursor = conn.cursor()
    
    # Get all segment IDs
    cursor.execute("SELECT id FROM signal_segments")
    segment_ids = [row[0] for row in cursor.fetchall()]
    
    # Available platforms
    platforms = ['the-trade-desk', 'index-exchange', 'openx', 'pubmatic']
    
    # Clear existing deployments
    cursor.execute("DELETE FROM platform_deployments")
    print(f"Cleared existing {cursor.rowcount} deployments")
    
    # Generate random deployments
    total_deployments = 0
    now = datetime.now().isoformat()
    
    for segment_id in segment_ids:
        # Random number of platforms for this segment (1-4)
        num_platforms = random.choices(
            [1, 2, 3, 4], 
            weights=[0.3, 0.4, 0.2, 0.1]  # 30% 1 platform, 40% 2 platforms, 20% 3 platforms, 10% all 4
        )[0]
        
        # Randomly select platforms
        selected_platforms = random.sample(platforms, num_platforms)
        
        for platform in selected_platforms:
            # Generate platform-specific segment ID
            platform_segment_id = f"{platform[:3]}_{segment_id}_{random.randint(100, 999)}"
            
            # Random scope (mostly platform-wide, some account-specific)
            scope = random.choices(['platform-wide', 'account-specific'], weights=[0.8, 0.2])[0]
            
            # Random live status (mostly live)
            is_live = random.choices([1, 0], weights=[0.9, 0.1])[0]
            
            # Random account (some have accounts, some don't)
            account = None
            if random.random() < 0.3:  # 30% have accounts
                account = f"brand-{random.randint(100, 999)}-{platform[:2]}"
            
            # Insert deployment
            cursor.execute("""
                INSERT INTO platform_deployments 
                (signals_agent_segment_id, platform, account, decisioning_platform_segment_id, 
                 scope, is_live, deployed_at, estimated_activation_duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                segment_id, platform, account, platform_segment_id,
                scope, is_live, now, 60
            ))
            total_deployments += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"Created {total_deployments} platform deployments for {len(segment_ids)} segments")
    
    # Show distribution
    conn = sqlite3.connect('signals_agent.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_segments,
            COUNT(CASE WHEN deployment_count = 1 THEN 1 END) as one_platform,
            COUNT(CASE WHEN deployment_count = 2 THEN 1 END) as two_platforms,
            COUNT(CASE WHEN deployment_count = 3 THEN 1 END) as three_platforms,
            COUNT(CASE WHEN deployment_count = 4 THEN 1 END) as all_platforms
        FROM (
            SELECT signals_agent_segment_id, COUNT(*) as deployment_count
            FROM platform_deployments
            GROUP BY signals_agent_segment_id
        )
    """)
    
    result = cursor.fetchone()
    print(f"\nDistribution:")
    print(f"  Total segments: {result[0]}")
    print(f"  1 platform: {result[1]} segments")
    print(f"  2 platforms: {result[2]} segments") 
    print(f"  3 platforms: {result[3]} segments")
    print(f"  All 4 platforms: {result[4]} segments")
    
    # Show platform breakdown
    cursor.execute("""
        SELECT platform, COUNT(*) as deployments
        FROM platform_deployments
        GROUP BY platform
        ORDER BY deployments DESC
    """)
    
    print(f"\nPlatform breakdown:")
    for platform, count in cursor.fetchall():
        print(f"  {platform}: {count} deployments")
    
    conn.close()

if __name__ == "__main__":
    update_platform_deployments()
