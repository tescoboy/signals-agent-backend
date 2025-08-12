#!/usr/bin/env python3
"""Script to update coverage percentages to be more varied."""

import sqlite3
import random
import os


def update_coverage_percentages():
    """Update coverage percentages to be more varied."""
    
    # Connect to database
    db_path = os.environ.get('DATABASE_PATH', 'signals_agent.db')
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()
    
    # Get all segment IDs
    cursor.execute("SELECT id FROM signal_segments")
    segments = cursor.fetchall()
    
    print(f"Updating coverage percentages for {len(segments)} segments...")
    
    # Update each segment with a random coverage percentage
    for i, (segment_id,) in enumerate(segments):
        # Generate a realistic coverage percentage between 1% and 50%
        coverage = random.uniform(1.0, 50.0)
        
        cursor.execute(
            "UPDATE signal_segments SET coverage_percentage = ? WHERE id = ?",
            (coverage, segment_id)
        )
        
        if (i + 1) % 100 == 0:
            print(f"Updated {i + 1} segments...")
    
    conn.commit()
    conn.close()
    
    print("Successfully updated coverage percentages!")
    
    # Verify the update
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(coverage_percentage), MAX(coverage_percentage), AVG(coverage_percentage) FROM signal_segments")
    min_coverage, max_coverage, avg_coverage = cursor.fetchone()
    conn.close()
    
    print(f"Coverage range: {min_coverage:.1f}% - {max_coverage:.1f}% (avg: {avg_coverage:.1f}%)")


if __name__ == "__main__":
    update_coverage_percentages()
