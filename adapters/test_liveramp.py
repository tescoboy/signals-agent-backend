"""Test LiveRamp adapter with simulated responses."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .liveramp import LiveRampAdapter


class TestLiveRampAdapter(LiveRampAdapter):
    """Test adapter for LiveRamp with simulated API responses."""
    
    def __init__(self, config: Dict[str, Any]):
        # Initialize without requiring real credentials in test mode
        self.config = config
        self.base_url = config.get('base_url', 'https://api.liveramp.com')
        self.cache = {}
        self.cache_duration = config.get('cache_duration_seconds', 60)
        self.auth_token = "test_token_12345"
        self.token_expires_at = datetime.now().timestamp() + 3600
    
    def authenticate(self) -> Dict[str, Any]:
        """Simulate successful authentication."""
        return {
            'access_token': self.auth_token,
            'expires_at': self.token_expires_at
        }
    
    def get_segments(self, account_id: str, principal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return simulated LiveRamp segments."""
        
        # Simulate diverse marketplace segments
        test_segments = [
            {
                'id': 'lr_seg_001',
                'name': 'High Net Worth Individuals',
                'description': 'Households with estimated net worth over $1M',
                'seller': {
                    'id': 'seller_001',
                    'name': 'Acxiom'
                },
                'pricing': {
                    'type': 'CPM',
                    'value': 12.50
                },
                'audience': {
                    'reach': {
                        'value': 15000000,  # 15M reach
                        'type': 'HOUSEHOLDS'
                    }
                },
                'categories': [
                    {'id': 'cat_001', 'name': 'Financial Services'},
                    {'id': 'cat_002', 'name': 'Wealth'}
                ]
            },
            {
                'id': 'lr_seg_002',
                'name': 'In-Market Auto Buyers - Luxury',
                'description': 'Consumers actively shopping for luxury vehicles',
                'seller': {
                    'id': 'seller_002',
                    'name': 'Experian'
                },
                'pricing': {
                    'type': 'CPM',
                    'value': 8.75
                },
                'audience': {
                    'reach': {
                        'value': 3500000,  # 3.5M reach
                        'type': 'INDIVIDUALS'
                    }
                },
                'categories': [
                    {'id': 'cat_003', 'name': 'Automotive'},
                    {'id': 'cat_004', 'name': 'In-Market'}
                ]
            },
            {
                'id': 'lr_seg_003',
                'name': 'Travel Enthusiasts - International',
                'description': 'Frequent international travelers with high travel spend',
                'seller': {
                    'id': 'seller_003',
                    'name': 'Oracle Data Cloud'
                },
                'pricing': {
                    'type': 'CPM',
                    'value': 6.25
                },
                'audience': {
                    'reach': {
                        'value': 8000000,  # 8M reach
                        'type': 'INDIVIDUALS'
                    }
                },
                'categories': [
                    {'id': 'cat_005', 'name': 'Travel'},
                    {'id': 'cat_006', 'name': 'Lifestyle'}
                ]
            },
            {
                'id': 'lr_seg_004',
                'name': 'Health & Wellness Advocates',
                'description': 'Active consumers of health and wellness products',
                'seller': {
                    'id': 'seller_004',
                    'name': 'Crossix'
                },
                'pricing': {
                    'type': 'CPM',
                    'value': 5.50
                },
                'audience': {
                    'reach': {
                        'value': 25000000,  # 25M reach
                        'type': 'INDIVIDUALS'
                    }
                },
                'categories': [
                    {'id': 'cat_007', 'name': 'Health'},
                    {'id': 'cat_008', 'name': 'Wellness'}
                ]
            },
            {
                'id': 'lr_seg_005',
                'name': 'Parents with Young Children',
                'description': 'Households with children under 12',
                'seller': {
                    'id': 'seller_001',
                    'name': 'Acxiom'
                },
                'pricing': {
                    'type': 'FREE',
                    'value': 0
                },
                'audience': {
                    'reach': {
                        'value': 30000000,  # 30M reach
                        'type': 'HOUSEHOLDS'
                    }
                },
                'categories': [
                    {'id': 'cat_009', 'name': 'Demographics'},
                    {'id': 'cat_010', 'name': 'Family'}
                ]
            }
        ]
        
        # Normalize and return
        return self._normalize_segments(test_segments, account_id)
    
    def activate_segment(self, segment_id: str, account_id: str, activation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate segment activation."""
        return {
            'platform_activation_id': f"lr_act_{segment_id}_{datetime.now().timestamp()}",
            'status': 'activating',
            'estimated_duration_minutes': 15,
            'activation_started_at': datetime.now().isoformat()
        }
    
    def check_segment_status(self, segment_id: str, account_id: str) -> Dict[str, Any]:
        """Simulate checking segment status."""
        # For demo, always return deployed
        return {
            'status': 'deployed',
            'is_live': True,
            'deployed_at': datetime.now().isoformat(),
            'platform_segment_id': segment_id
        }