"""Test Index Exchange adapter with simulated responses."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import PlatformAdapter

class TestIndexExchangeAdapter(PlatformAdapter):
    """Test adapter that simulates Index Exchange API responses."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.username = config.get('username', 'test-user')
        self.password = config.get('password', 'test-pass')
        
        # Simulate Index Exchange segments
        self.mock_segments = [
            {
                "id": "ix_luxury_auto_123",
                "name": "Luxury Automotive Intenders - IX",
                "description": "Users browsing luxury car content on premium automotive sites",
                "category": "Automotive - Luxury",
                "type": "behavioral",
                "reach": 2500000,
                "pricing": 7.25
            },
            {
                "id": "ix_auto_shopping_456", 
                "name": "Auto Shopping - Research Phase",
                "description": "Users actively researching vehicle purchases",
                "category": "Automotive - Shopping",
                "type": "intent",
                "reach": 1800000,
                "pricing": 5.50
            },
            {
                "id": "ix_premium_lifestyle_789",
                "name": "Premium Lifestyle Consumers",
                "description": "High-income users interested in luxury goods and services",
                "category": "Lifestyle - Premium", 
                "type": "demographic",
                "reach": 3200000,
                "pricing": 8.75
            }
        ]
    
    def authenticate(self) -> Dict[str, Any]:
        """Simulate Index Exchange authentication."""
        return {
            'access_token': 'test_token_12345',
            'refresh_token': 'refresh_token_67890',
            'expires_at': datetime.now().timestamp() + 5400
        }
    
    def get_segments(self, account_id: str, principal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simulate fetching segments from Index Exchange."""
        # Validate principal access
        if principal_id and not self._validate_principal_access(principal_id, account_id):
            raise ValueError(f"Principal '{principal_id}' does not have access to account '{account_id}'")
        
        # Check cache first
        cache_key = f"test_ix_segments_{account_id}"
        cached_segments = self._get_from_cache(cache_key)
        if cached_segments:
            return cached_segments
        
        # Simulate API delay
        print(f"[Test Mode] Fetching segments from Index Exchange account {account_id}")
        
        # Normalize the mock segments
        segments = self._normalize_segments(self.mock_segments, account_id)
        
        # Cache the results
        self._set_cache(cache_key, segments)
        
        return segments
    
    def _normalize_segments(self, raw_segments: List[Dict], account_id: str) -> List[Dict[str, Any]]:
        """Normalize mock Index Exchange segments to our internal format."""
        normalized = []
        
        for segment in raw_segments:
            normalized_segment = {
                'id': f"ix_{account_id}_{segment['id']}",
                'platform_segment_id': segment['id'],
                'name': segment['name'],
                'description': segment['description'],
                'audience_type': self._map_segment_type(segment),
                'data_provider': 'Index Exchange (Test)',
                'coverage_percentage': self._estimate_coverage(segment),
                'base_cpm': segment.get('pricing', 5.00),
                'revenue_share_percentage': 0.0,
                'catalog_access': 'personalized',
                'platform': 'index-exchange',
                'account_id': account_id,
                'raw_data': segment
            }
            normalized.append(normalized_segment)
        
        return normalized
    
    def _map_segment_type(self, segment: Dict) -> str:
        """Map segment types to our taxonomy."""
        category = segment.get('category', '').lower()
        
        if 'automotive' in category:
            return 'automotive'
        elif 'lifestyle' in category:
            return 'lifestyle'
        elif 'financial' in category:
            return 'financial'
        else:
            return 'behavioral'
    
    def _estimate_coverage(self, segment: Dict) -> float:
        """Estimate coverage from reach data."""
        reach = segment.get('reach', 0)
        
        if reach > 3000000:
            return 28.0
        elif reach > 2000000:
            return 18.0
        elif reach > 1000000:
            return 12.0
        else:
            return 6.0
    
    def activate_segment(self, segment_id: str, account_id: str, activation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate segment activation."""
        return {
            'platform_activation_id': f"test_ix_activation_{segment_id}",
            'status': 'activating',
            'estimated_duration_minutes': 10,
            'activation_started_at': datetime.now().isoformat()
        }
    
    def check_segment_status(self, segment_id: str, account_id: str) -> Dict[str, Any]:
        """Simulate segment status check."""
        return {
            'status': 'deployed',
            'is_live': True,
            'deployed_at': datetime.now().isoformat(),
            'platform_segment_id': segment_id
        }