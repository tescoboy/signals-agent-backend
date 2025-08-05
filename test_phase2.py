#!/usr/bin/env python3
"""Test script for Phase 2 features."""

import sqlite3
import json
from datetime import datetime, timedelta

def test_context_storage():
    """Test that context storage is working correctly."""
    conn = sqlite3.connect('signals_agent.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('discovery_contexts', 'activation_contexts')")
    tables = [row['name'] for row in cursor.fetchall()]
    
    print("✅ Context tables created:", tables)
    
    # Check discovery contexts
    cursor.execute("SELECT * FROM discovery_contexts")
    contexts = cursor.fetchall()
    
    if contexts:
        print(f"\n✅ Found {len(contexts)} discovery context(s):")
        for ctx in contexts:
            print(f"  - Context ID: {ctx['context_id']}")
            print(f"    Query: {ctx['query']}")
            print(f"    Created: {ctx['created_at']}")
            print(f"    Expires: {ctx['expires_at']}")
            
            # Check expiration
            expires = datetime.fromisoformat(ctx['expires_at'])
            days_until_expiry = (expires - datetime.now()).days
            print(f"    Days until expiry: {days_until_expiry}")
    else:
        print("\n⚠️  No discovery contexts found yet (run a discovery first)")
    
    # Check activation contexts
    cursor.execute("SELECT * FROM activation_contexts")
    activations = cursor.fetchall()
    
    if activations:
        print(f"\n✅ Found {len(activations)} activation context(s):")
        for act in activations:
            print(f"  - Signal: {act['signal_id']} on {act['platform']}")
            print(f"    Linked to context: {act['context_id']}")
            print(f"    Activated at: {act['activated_at']}")
    else:
        print("\n⚠️  No activation contexts found yet (activate a signal with context_id)")
    
    conn.close()

if __name__ == "__main__":
    print("🧪 Testing Phase 2 Context Storage Features\n")
    test_context_storage()