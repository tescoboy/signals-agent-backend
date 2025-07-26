"""Configuration loader with environment variable support."""

import os
import json
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json with environment variable overrides.
    
    Environment variables:
    - GEMINI_API_KEY: Overrides gemini_api_key
    - IX_USERNAME: Overrides platforms.index-exchange.username
    - IX_PASSWORD: Overrides platforms.index-exchange.password
    - IX_ACCOUNT_MAPPING: JSON string for principal account mappings
    """
    # Load base config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        # If no config.json, start with sample
        with open('config.json.sample', 'r') as f:
            config = json.load(f)
    
    # Override with environment variables
    if gemini_key := os.environ.get('GEMINI_API_KEY'):
        config['gemini_api_key'] = gemini_key
    
    # Platform-specific overrides
    if 'platforms' in config:
        # Index Exchange overrides
        if 'index-exchange' in config['platforms']:
            if ix_username := os.environ.get('IX_USERNAME'):
                config['platforms']['index-exchange']['username'] = ix_username
            
            if ix_password := os.environ.get('IX_PASSWORD'):
                config['platforms']['index-exchange']['password'] = ix_password
            
            # Account mappings (JSON string)
            if ix_mappings := os.environ.get('IX_ACCOUNT_MAPPING'):
                try:
                    mappings = json.loads(ix_mappings)
                    config['platforms']['index-exchange']['principal_accounts'] = mappings
                except json.JSONDecodeError:
                    print(f"Warning: Invalid IX_ACCOUNT_MAPPING JSON: {ix_mappings}")
        
        # LiveRamp overrides
        if 'liveramp' in config['platforms']:
            if lr_client_id := os.environ.get('LIVERAMP_CLIENT_ID'):
                config['platforms']['liveramp']['client_id'] = lr_client_id
            
            if lr_client_secret := os.environ.get('LIVERAMP_CLIENT_SECRET'):
                config['platforms']['liveramp']['client_secret'] = lr_client_secret
            
            # Account mappings (JSON string)
            if lr_mappings := os.environ.get('LIVERAMP_ACCOUNT_MAPPING'):
                try:
                    mappings = json.loads(lr_mappings)
                    config['platforms']['liveramp']['principal_accounts'] = mappings
                except json.JSONDecodeError:
                    print(f"Warning: Invalid LIVERAMP_ACCOUNT_MAPPING JSON: {lr_mappings}")
    
    # Database path override (useful for Docker volumes)
    if db_path := os.environ.get('DATABASE_PATH'):
        config['database']['path'] = db_path
    
    return config

def get_secret(key: str, default: str = None) -> str:
    """Get a secret from environment or config."""
    return os.environ.get(key, default)