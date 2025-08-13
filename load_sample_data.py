#!/usr/bin/env python3
"""Script to load all signals from sample_data.json into the database."""

import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any


def load_sample_data():
    """Load all signals from sample_data.json into the database."""
    
    # Read the sample data
    with open('sample_data.json', 'r') as f:
        data = json.load(f)
    
    print(f"Found {data['totalCount']} signals in sample_data.json")
    
    # Connect to database
    db_path = os.environ.get('DATABASE_PATH', 'signals_agent.db')
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()
    
    # Clear existing signal segments
    cursor.execute("DELETE FROM signal_segments")
    print("Cleared existing signal segments")
    
    # Insert all signals
    now = datetime.now().isoformat()
    inserted_count = 0
    
    for segment in data['segments']:
        try:
            # Extract data provider name from the object
            data_provider = segment.get('dataProvider', {})
            if isinstance(data_provider, dict):
                data_provider_name = data_provider.get('name', 'Unknown')
            else:
                data_provider_name = str(data_provider)
            
            # OVERRIDE: Always use HarvinAds as data provider
            data_provider_name = 'HarvinAds'
            
            # Map the sample data structure to our database schema
            cursor.execute("""
                INSERT INTO signal_segments (
                    id, name, description, data_provider, coverage_percentage,
                    signal_type, catalog_access, base_cpm, revenue_share_percentage,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(segment.get('segmentID', f"segment_{inserted_count}")),
                segment.get('externalSegmentName', 'Unknown Segment'),
                f"Segment from {data_provider_name}",
                data_provider_name,
                25.0,  # Default coverage percentage
                'audience',  # Default signal type
                'public',  # Default catalog access
                5.0,  # Default CPM
                15.0,  # Default revenue share
                now,
                now
            ))
            inserted_count += 1
            
            if inserted_count % 100 == 0:
                print(f"Inserted {inserted_count} signals...")
                
        except sqlite3.IntegrityError as e:
            print(f"Error inserting segment {segment.get('segmentID', 'unknown')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"Successfully loaded {inserted_count} signals into the database!")
    
    # Verify the count
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM signal_segments")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Database now contains {count} signal segments")


if __name__ == "__main__":
    load_sample_data()
