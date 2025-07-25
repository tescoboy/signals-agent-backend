#!/usr/bin/env python3
"""Parse Peer39 segments from Index Exchange sample data."""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any


def extract_peer39_segments(json_file: str) -> List[Dict[str, Any]]:
    """Extract Peer39 segments from Index Exchange JSON data."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    peer39_segments = []
    
    for segment in data.get('segments', []):
        # Only process Peer39 segments
        if segment.get('dataProvider', {}).get('name') != 'Peer39':
            continue
            
        # Skip if segment is not active
        if segment.get('segmentStatus') != 'A':
            continue
        
        segment_name = segment.get('externalSegmentName', '')
        if not segment_name:
            continue
        
        # Generate our internal segment ID
        internal_id = f"peer39_{segment['segmentID']}"
        
        # Estimate coverage percentage based on category breadth
        coverage_percentage = estimate_coverage(segment_name)
        
        # Determine CPM based on category value
        cpm = estimate_cpm(segment_name)
        
        peer39_segments.append({
            'id': internal_id,
            'name': segment_name,
            'description': generate_description(segment_name),
            'data_provider': 'Peer39',
            'coverage_percentage': coverage_percentage,
            'audience_type': 'marketplace',
            'catalog_access': 'public',
            'base_cpm': cpm,
            'revenue_share_percentage': 12.0,
            'ix_segment_id': segment['segmentID'],
            'ix_audience_id': segment['audienceID']
        })
    
    return peer39_segments


def estimate_coverage(segment_name: str) -> float:
    """Estimate coverage percentage based on segment name."""
    # More specific segments = lower coverage
    if ':' not in segment_name:
        # Top-level categories (e.g., "Automotive", "Business")
        return round(35.0 + (hash(segment_name) % 20), 1)  # 35-55%
    
    depth = segment_name.count(':')
    if depth == 1:
        # Second-level (e.g., "Automotive : Manufacturers")
        return round(15.0 + (hash(segment_name) % 20), 1)  # 15-35%
    elif depth == 2:
        # Third-level (e.g., "Automotive : Manufacturers : BMW")
        return round(3.0 + (hash(segment_name) % 12), 1)   # 3-15%
    else:
        # Very specific (e.g., "Arts and Entertainment : Celebrities : Royal Baby")
        return round(0.5 + (hash(segment_name) % 5), 1)    # 0.5-5.5%


def estimate_cpm(segment_name: str) -> float:
    """Estimate CPM based on segment category and specificity."""
    name_lower = segment_name.lower()
    
    # Premium categories
    if any(keyword in name_lower for keyword in ['luxury', 'premium', 'high-end', 'exclusive']):
        base_cpm = 4.50
    elif any(keyword in name_lower for keyword in ['automotive', 'vehicles', 'cars']):
        base_cpm = 3.25
    elif any(keyword in name_lower for keyword in ['finance', 'investment', 'banking', 'insurance']):
        base_cpm = 3.75
    elif any(keyword in name_lower for keyword in ['technology', 'tech', 'software', 'computing']):
        base_cpm = 3.00
    elif any(keyword in name_lower for keyword in ['business', 'b2b', 'enterprise']):
        base_cpm = 2.75
    elif any(keyword in name_lower for keyword in ['travel', 'vacation', 'tourism']):
        base_cpm = 2.50
    else:
        base_cpm = 2.25
    
    # Adjust for specificity (more specific = higher CPM)
    depth = segment_name.count(':')
    specificity_multiplier = 1.0 + (depth * 0.15)
    
    final_cpm = base_cpm * specificity_multiplier
    return round(final_cpm, 2)


def generate_description(segment_name: str) -> str:
    """Generate a description based on the segment name."""
    parts = [part.strip() for part in segment_name.split(':')]
    
    if len(parts) == 1:
        return f"Contextual audience interested in {parts[0].lower()} content"
    elif len(parts) == 2:
        return f"Contextual audience for {parts[1].lower()} within {parts[0].lower()}"
    else:
        return f"Highly targeted contextual audience for {parts[-1].lower()} content"


def update_database_with_peer39(segments: List[Dict[str, Any]]):
    """Update the database with realistic Peer39 segments."""
    conn = sqlite3.connect('audience_agent.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Clear existing Peer39 segments
    cursor.execute("DELETE FROM audience_segments WHERE data_provider = 'Peer39'")
    cursor.execute("DELETE FROM platform_deployments WHERE audience_agent_segment_id LIKE 'peer39_%'")
    
    # Insert new segments
    for segment in segments[:50]:  # Limit to 50 segments for demo
        cursor.execute("""
            INSERT INTO audience_segments 
            (id, name, description, data_provider, coverage_percentage, 
             audience_type, catalog_access, base_cpm, revenue_share_percentage, 
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment['id'], segment['name'], segment['description'], 
            segment['data_provider'], segment['coverage_percentage'],
            segment['audience_type'], segment['catalog_access'],
            segment['base_cpm'], segment['revenue_share_percentage'],
            now, now
        ))
        
        # Add Index Exchange deployment (live)
        cursor.execute("""
            INSERT INTO platform_deployments 
            (audience_agent_segment_id, platform, account, decisioning_platform_segment_id,
             scope, is_live, deployed_at, estimated_activation_duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment['id'], 'index-exchange', None,
            f"ix_peer39_{segment['ix_segment_id']}", 'platform-wide', 
            True, now, 60
        ))
        
        # Add other platform deployments (some live, some not)
        platforms_config = [
            ('the-trade-desk', True, f"ttd_peer39_{segment['ix_segment_id']}"),
            ('openx', True, f"ox_peer39_{segment['ix_segment_id']}"),
            ('pubmatic', False, None),  # Needs activation
            ('google-dv360', False, None),  # Needs activation
        ]
        
        for platform, is_live, segment_id in platforms_config:
            cursor.execute("""
                INSERT INTO platform_deployments 
                (audience_agent_segment_id, platform, account, decisioning_platform_segment_id,
                 scope, is_live, deployed_at, estimated_activation_duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                segment['id'], platform, None, segment_id, 'platform-wide',
                is_live, now if is_live else None, 60
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated database with {len(segments[:50])} Peer39 segments")


def main():
    """Main function to parse and update database."""
    print("🔄 Parsing Peer39 segments from Index Exchange data...")
    
    try:
        segments = extract_peer39_segments('sample_data.json')
        print(f"📊 Found {len(segments)} Peer39 segments")
        
        # Show some examples
        print("\n📋 Sample segments:")
        for i, segment in enumerate(segments[:5]):
            print(f"  {i+1}. {segment['name']} (Coverage: {segment['coverage_percentage']}%, CPM: ${segment['base_cpm']})")
        
        print("\n🗄️  Updating database...")
        update_database_with_peer39(segments)
        
        print("\n✅ Database updated! You can now test with queries like:")
        print("   • 'luxury automotive content'")
        print("   • 'BMW car shoppers'") 
        print("   • 'electric vehicle interest'")
        print("   • 'business and technology content'")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()