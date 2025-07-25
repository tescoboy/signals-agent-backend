"""Database initialization and sample data for the Audience Agent."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any


def init_db():
    """Initialize the database with tables and sample data."""
    conn = sqlite3.connect('audience_agent.db')
    cursor = conn.cursor()
    
    # Create tables
    create_tables(cursor)
    
    # Insert sample data
    insert_sample_data(cursor)
    
    conn.commit()
    conn.close()
    print("Database initialized with sample data")


def create_tables(cursor: sqlite3.Cursor):
    """Create all database tables."""
    
    # Audience segments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audience_segments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            data_provider TEXT NOT NULL,
            coverage_percentage REAL NOT NULL,
            audience_type TEXT NOT NULL CHECK (audience_type IN ('private', 'marketplace')),
            catalog_access TEXT NOT NULL CHECK (catalog_access IN ('public', 'personalized', 'private')),
            base_cpm REAL NOT NULL,
            revenue_share_percentage REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Platform deployments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audience_agent_segment_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            account TEXT,
            decisioning_platform_segment_id TEXT,
            scope TEXT NOT NULL CHECK (scope IN ('platform-wide', 'account-specific')),
            is_live BOOLEAN NOT NULL DEFAULT 0,
            deployed_at TEXT,
            estimated_activation_duration_minutes INTEGER NOT NULL DEFAULT 60,
            FOREIGN KEY (audience_agent_segment_id) REFERENCES audience_segments (id),
            UNIQUE(audience_agent_segment_id, platform, account)
        )
    """)
    


def insert_sample_data(cursor: sqlite3.Cursor):
    """Insert sample audience segments and platform deployments."""
    
    now = datetime.now().isoformat()
    
    # Sample audience segments
    segments = [
        {
            'id': 'sports_enthusiasts_public',
            'name': 'Sports Enthusiasts - Public',
            'description': 'Broad sports audience available platform-wide',
            'data_provider': 'Polk',
            'coverage_percentage': 45.0,
            'audience_type': 'marketplace',
            'catalog_access': 'public',
            'base_cpm': 3.50,
            'revenue_share_percentage': 15.0,
        },
        {
            'id': 'luxury_auto_intenders',
            'name': 'Luxury Automotive Intenders',
            'description': 'High-income individuals showing luxury car purchase intent',
            'data_provider': 'Experian',
            'coverage_percentage': 12.5,
            'audience_type': 'marketplace',
            'catalog_access': 'personalized',
            'base_cpm': 8.75,
            'revenue_share_percentage': 20.0,
        },
        {
            'id': 'peer39_luxury_auto',
            'name': 'Luxury Automotive Context',
            'description': 'Pages with luxury automotive content and high viewability',
            'data_provider': 'Peer39',
            'coverage_percentage': 15.0,
            'audience_type': 'marketplace',
            'catalog_access': 'public',
            'base_cpm': 2.50,
            'revenue_share_percentage': 12.0,
        },
        {
            'id': 'running_gear_premium',
            'name': 'Premium Running Gear Buyers',
            'description': 'High-income consumers who purchase premium athletic equipment',
            'data_provider': 'Acxiom',
            'coverage_percentage': 8.3,
            'audience_type': 'marketplace',
            'catalog_access': 'personalized',
            'base_cpm': 6.25,
            'revenue_share_percentage': 18.0,
        },
        {
            'id': 'urban_millennials',
            'name': 'Urban Millennials',
            'description': 'Millennials living in major urban markets with disposable income',
            'data_provider': 'LiveRamp',
            'coverage_percentage': 32.0,
            'audience_type': 'marketplace',
            'catalog_access': 'public',
            'base_cpm': 4.00,
            'revenue_share_percentage': 15.0,
        },
        {
            'id': 'private_customer_segments',
            'name': 'Private Customer Segments',
            'description': 'Proprietary first-party audience segments',
            'data_provider': 'Internal',
            'coverage_percentage': 100.0,
            'audience_type': 'private',
            'catalog_access': 'private',
            'base_cpm': 0.00,
            'revenue_share_percentage': None,
        }
    ]
    
    for segment in segments:
        cursor.execute("""
            INSERT OR REPLACE INTO audience_segments 
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
    
    # Sample platform deployments
    deployments = [
        # Sports enthusiasts - already live on multiple platforms
        {
            'audience_agent_segment_id': 'sports_enthusiasts_public',
            'platform': 'the-trade-desk',
            'account': None,
            'decisioning_platform_segment_id': 'ttd_sports_general',
            'scope': 'platform-wide',
            'is_live': True,
            'deployed_at': now,
            'estimated_activation_duration_minutes': 60
        },
        {
            'audience_agent_segment_id': 'sports_enthusiasts_public',
            'platform': 'index-exchange',
            'account': None,
            'decisioning_platform_segment_id': 'ix_sports_enthusiasts_public',
            'scope': 'platform-wide',
            'is_live': True,
            'deployed_at': now,
            'estimated_activation_duration_minutes': 60
        },
        
        # Luxury auto - mix of live and requiring activation
        {
            'audience_agent_segment_id': 'peer39_luxury_auto',
            'platform': 'index-exchange',
            'account': None,
            'decisioning_platform_segment_id': 'ix_peer39_luxury_auto_gen',
            'scope': 'platform-wide',
            'is_live': True,
            'deployed_at': now,
            'estimated_activation_duration_minutes': 60
        },
        {
            'audience_agent_segment_id': 'peer39_luxury_auto',
            'platform': 'openx',
            'account': None,
            'decisioning_platform_segment_id': 'ox_peer39_lux_auto_456',
            'scope': 'platform-wide',
            'is_live': True,
            'deployed_at': now,
            'estimated_activation_duration_minutes': 60
        },
        {
            'audience_agent_segment_id': 'peer39_luxury_auto',
            'platform': 'pubmatic',
            'account': 'brand-456-pm',
            'decisioning_platform_segment_id': None,
            'scope': 'account-specific',
            'is_live': False,
            'deployed_at': None,
            'estimated_activation_duration_minutes': 60
        },
        {
            'audience_agent_segment_id': 'peer39_luxury_auto',
            'platform': 'index-exchange',
            'account': 'agency-123-ix',
            'decisioning_platform_segment_id': 'ix_agency123_peer39_lux_auto',
            'scope': 'account-specific',
            'is_live': True,
            'deployed_at': now,
            'estimated_activation_duration_minutes': 60
        },
        
        # Urban millennials - live on TTD
        {
            'audience_agent_segment_id': 'urban_millennials',
            'platform': 'the-trade-desk',
            'account': None,
            'decisioning_platform_segment_id': 'ttd_urban_millennials_gen',
            'scope': 'platform-wide',
            'is_live': True,
            'deployed_at': now,
            'estimated_activation_duration_minutes': 60
        },
        
        # Premium running gear - personalized, requiring activation
        {
            'audience_agent_segment_id': 'running_gear_premium',
            'platform': 'the-trade-desk',
            'account': 'omnicom-ttd-main',
            'decisioning_platform_segment_id': None,
            'scope': 'account-specific',
            'is_live': False,
            'deployed_at': None,
            'estimated_activation_duration_minutes': 120
        }
    ]
    
    for deployment in deployments:
        cursor.execute("""
            INSERT OR REPLACE INTO platform_deployments 
            (audience_agent_segment_id, platform, account, decisioning_platform_segment_id,
             scope, is_live, deployed_at, estimated_activation_duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deployment['audience_agent_segment_id'], deployment['platform'],
            deployment['account'], deployment['decisioning_platform_segment_id'],
            deployment['scope'], deployment['is_live'], deployment['deployed_at'],
            deployment['estimated_activation_duration_minutes']
        ))


if __name__ == "__main__":
    init_db()