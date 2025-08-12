#!/usr/bin/env python3
"""
Load Peer39 segments from sample_data.json into the signal_segments table.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any


def extract_peer39_segments(json_file: str) -> List[Dict[str, Any]]:
    """Extract Peer39 segments from the JSON file."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    segments = []
    for segment in data.get('segments', []):
        # Extract relevant fields from Peer39 data
        name = segment.get('externalSegmentName', 'Unknown Segment')
        description = f"Peer39 contextual segment: {name}"
        coverage = segment.get('coveragePercentage', 5.0)
        cpm = segment.get('cpm', 2.50)
        
        # Create segment ID
        segment_id = f"peer39_{segment.get('segmentID', 'unknown')}"
        
        segments.append({
            'id': segment_id,
            'name': name,
            'description': description,
            'data_provider': 'Peer39',
            'coverage_percentage': coverage,
            'signal_type': 'contextual',
            'catalog_access': 'public',
            'base_cpm': cpm,
            'revenue_share_percentage': 15.0,
            'ix_segment_id': segment.get('segmentID', 'unknown')
        })
    
    return segments


def update_database_with_peer39(segments: List[Dict[str, Any]]):
    """Update the database with Peer39 segments."""
    conn = sqlite3.connect('signals_agent.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Clear existing Peer39 segments
    cursor.execute("DELETE FROM signal_segments WHERE data_provider = 'Peer39'")
    cursor.execute("DELETE FROM platform_deployments WHERE signals_agent_segment_id LIKE 'peer39_%'")
    
    # Insert new segments
    for segment in segments:
        cursor.execute("""
            INSERT INTO signal_segments 
            (id, name, description, data_provider, coverage_percentage, 
             signal_type, catalog_access, base_cpm, revenue_share_percentage, 
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment['id'], segment['name'], segment['description'], 
            segment['data_provider'], segment['coverage_percentage'],
            segment['signal_type'], segment['catalog_access'],
            segment['base_cpm'], segment['revenue_share_percentage'],
            now, now
        ))
        
        # Add Index Exchange deployment (live)
        cursor.execute("""
            INSERT INTO platform_deployments 
            (signals_agent_segment_id, platform, account, decisioning_platform_segment_id,
             scope, is_live, deployed_at, estimated_activation_duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment['id'], 'index-exchange', None,
            f"ix_peer39_{segment['ix_segment_id']}", 'platform-wide', 
            True, now, 60
        ))
        
        # Add other platform deployments
        platforms_config = [
            ('the-trade-desk', True, f"ttd_peer39_{segment['ix_segment_id']}"),
            ('openx', True, f"ox_peer39_{segment['ix_segment_id']}"),
            ('pubmatic', False, None),
            ('google-dv360', False, None),
        ]
        
        for platform, is_live, segment_id in platforms_config:
            cursor.execute("""
                INSERT INTO platform_deployments 
                (signals_agent_segment_id, platform, account, decisioning_platform_segment_id,
                 scope, is_live, deployed_at, estimated_activation_duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                segment['id'], platform, None, segment_id, 'platform-wide',
                is_live, now if is_live else None, 60
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated database with {len(segments)} Peer39 segments")


def main():
    """Main function to parse and update database."""
    print("🔄 Loading Peer39 segments from sample_data.json...")
    
    try:
        segments = extract_peer39_segments('sample_data.json')
        print(f"📊 Found {len(segments)} Peer39 segments")
        
        # Show some examples
        print("\n📋 Sample segments:")
        for i, segment in enumerate(segments[:5]):
            print(f"  {i+1}. {segment['name']} (Coverage: {segment['coverage_percentage']}%, CPM: ${segment['base_cpm']})")
        
        print("\n🗄️  Updating database...")
        update_database_with_peer39(segments)
        
        # Verify the count
        conn = sqlite3.connect('signals_agent.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signal_segments WHERE data_provider = 'Peer39'")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"\n✅ Database now contains {count} Peer39 segments!")
        print("\n🎯 You can now test with queries like:")
        print("   • 'sports enthusiasts'")
        print("   • 'luxury automotive content'")
        print("   • 'business and technology'")
        print("   • 'arts and entertainment'")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
