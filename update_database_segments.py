#!/usr/bin/env python3
"""
Update database.py with 575 segments from sample_data.json
"""

import json
import random

def update_database_segments():
    """Update database.py with 575 segments from sample_data.json"""
    
    # Load the sample data
    with open('sample_data.json', 'r') as f:
        data = json.load(f)
    
    segments = data['segments']
    print(f"Converting {len(segments)} segments...")
    
    # Convert to database.py format
    db_segments = []
    
    for segment in segments:
        # Extract data provider name
        data_provider = segment.get('dataProvider', {})
        if isinstance(data_provider, dict):
            data_provider_name = data_provider.get('name', 'Peer39')
        else:
            data_provider_name = str(data_provider)
        
        # Generate random coverage percentage (1.0% - 50.0%)
        coverage_percentage = random.uniform(1.0, 50.0)
        
        # Generate random CPM (1.0 - 10.0)
        base_cpm = random.uniform(1.0, 10.0)
        
        # Create database segment format
        db_segment = {
            'id': str(segment.get('segmentID', f"segment_{len(db_segments)}")),
            'name': segment.get('externalSegmentName', 'Unknown Segment'),
            'description': f"Segment from {data_provider_name}",
            'data_provider': data_provider_name,
            'coverage_percentage': coverage_percentage,
            'signal_type': 'audience',  # Default to audience
            'catalog_access': 'public',  # Default to public
            'base_cpm': base_cpm,
            'revenue_share_percentage': 15.0,  # Default revenue share
        }
        
        db_segments.append(db_segment)
    
    # Read the current database.py file
    with open('database.py', 'r') as f:
        content = f.read()
    
    # Create the new segments list as a string
    segments_str = "[\n"
    for segment in db_segments:
        segments_str += f"""        {{
            'id': '{segment['id']}',
            'name': '{segment['name']}',
            'description': '{segment['description']}',
            'data_provider': '{segment['data_provider']}',
            'coverage_percentage': {segment['coverage_percentage']},
            'signal_type': '{segment['signal_type']}',
            'catalog_access': '{segment['catalog_access']}',
            'base_cpm': {segment['base_cpm']},
            'revenue_share_percentage': {segment['revenue_share_percentage']},
        }},\n"""
    segments_str += "    ]"
    
    # Find and replace the segments list in database.py
    # Look for the start of the segments list
    start_marker = "    # Sample signal segments\n    segments = ["
    end_marker = "    ]"
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("Could not find segments list in database.py")
        return
    
    # Find the end of the segments list
    end_pos = content.find(end_marker, start_pos)
    if end_pos == -1:
        print("Could not find end of segments list in database.py")
        return
    
    # Replace the segments list
    new_content = content[:start_pos] + "    # Sample signal segments\n    segments = " + segments_str + content[end_pos + len(end_marker):]
    
    # Write the updated content back to database.py
    with open('database.py', 'w') as f:
        f.write(new_content)
    
    print(f"Updated database.py with {len(db_segments)} segments")
    
    # Print sample segments
    print("\nSample segments:")
    for i, segment in enumerate(db_segments[:5]):
        print(f"  {i+1}. {segment['name']} (ID: {segment['id']})")

if __name__ == "__main__":
    update_database_segments()
