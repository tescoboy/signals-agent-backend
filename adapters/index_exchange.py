"""Index Exchange platform adapter."""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import PlatformAdapter

class IndexExchangeAdapter(PlatformAdapter):
    """Adapter for Index Exchange audience API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://app.indexexchange.com/api')
        self.username = config.get('username')
        self.password = config.get('password')
        self.auth_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        if not self.username or not self.password:
            raise ValueError("Index Exchange adapter requires username and password in config")
    
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with Index Exchange and get access token."""
        # Check if we have a valid token in cache
        if self._is_token_valid():
            return {
                'access_token': self.auth_token,
                'expires_at': self.token_expires_at
            }
        
        # Try to refresh token first if available
        if self.refresh_token:
            try:
                return self._refresh_auth_token()
            except Exception:
                # If refresh fails, do full login
                pass
        
        # Full login
        login_url = f"{self.base_url}/authentication/v1/login"
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        response = requests.post(
            login_url,
            headers={
                'accept': 'application/json',
                'content-type': 'application/json'
            },
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Index Exchange authentication failed: {response.status_code} {response.text}")
        
        data = response.json()
        auth_response = data.get('loginResponse', {}).get('authResponse', {})
        
        self.auth_token = auth_response.get('access_token')
        self.refresh_token = auth_response.get('refresh_token')
        expires_in = auth_response.get('expires_in', 5400)  # Default 1.5 hours
        self.token_expires_at = datetime.now().timestamp() + expires_in
        
        return {
            'access_token': self.auth_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.token_expires_at
        }
    
    def _is_token_valid(self) -> bool:
        """Check if current auth token is still valid."""
        if not self.auth_token or not self.token_expires_at:
            return False
        
        # Add 5 minute buffer before expiration
        return datetime.now().timestamp() < (self.token_expires_at - 300)
    
    def _refresh_auth_token(self) -> Dict[str, Any]:
        """Refresh the authentication token."""
        refresh_url = f"{self.base_url}/authentication/v1/refresh"
        payload = {
            "refreshToken": self.refresh_token
        }
        
        response = requests.post(
            refresh_url,
            headers={
                'accept': 'application/json',
                'content-type': 'application/json'
            },
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.status_code} {response.text}")
        
        data = response.json()
        auth_response = data.get('authResponse', {})
        
        self.auth_token = auth_response.get('access_token')
        expires_in = auth_response.get('expires_in', 5400)
        self.token_expires_at = datetime.now().timestamp() + expires_in
        
        return {
            'access_token': self.auth_token,
            'expires_at': self.token_expires_at
        }
    
    def get_segments(self, account_id: str, principal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch audience segments from Index Exchange for the given account."""
        # Validate principal access to account
        if principal_id and not self._validate_principal_access(principal_id, account_id):
            raise ValueError(f"Principal '{principal_id}' does not have access to account '{account_id}'")
        
        # Check cache first
        cache_key = f"ix_segments_{account_id}"
        cached_segments = self._get_from_cache(cache_key)
        if cached_segments:
            return cached_segments
        
        # Ensure we have valid authentication
        self.authenticate()
        
        # Fetch segments from Index Exchange API
        segments_url = f"{self.base_url}/segments/v2/segments"
        params = {'accountID': account_id}
        
        response = requests.get(
            segments_url,
            headers={
                'Authorization': f'Bearer {self.auth_token}',
                'accept': 'application/json'
            },
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch segments: {response.status_code} {response.text}")
        
        data = response.json()
        segments = self._normalize_segments(data.get('segments', []), account_id)
        
        # Cache the results
        self._set_cache(cache_key, segments)
        
        return segments
    
    def _normalize_segments(self, raw_segments: List[Dict], account_id: str) -> List[Dict[str, Any]]:
        """Normalize Index Exchange segments to our internal format."""
        normalized = []
        
        for segment in raw_segments:
            # Extract relevant fields using Index Exchange API field names
            segment_id = segment.get('segmentID', segment.get('audienceID', 'unknown'))
            segment_name = segment.get('externalSegmentName', segment.get('name', f'IX Segment {segment_id}'))
            
            # Handle data provider - extract name from dict if needed
            data_provider_raw = segment.get('dataProvider', 'Index Exchange')
            if isinstance(data_provider_raw, dict):
                data_provider_name = data_provider_raw.get('name', 'Unknown Provider')
            else:
                data_provider_name = str(data_provider_raw)
            
            # Get coverage and CPM, use None if not available
            coverage = self._estimate_coverage(segment)
            cpm = self._estimate_cpm(segment)
            
            normalized_segment = {
                'id': f"ix_{account_id}_{segment_id}",
                'platform_segment_id': str(segment_id),  # Ensure it's a string
                'name': segment_name,
                'description': f"Index Exchange segment from {data_provider_name}",
                'audience_type': 'marketplace',  # Index Exchange segments are marketplace segments
                'data_provider': f"Index Exchange ({data_provider_name})",
                'coverage_percentage': coverage if coverage is not None else None,  # None for unknown
                'base_cpm': cpm if cpm is not None else 0.0,  # Use 0 for unknown/free
                'revenue_share_percentage': 0.0,  # Index Exchange typically uses CPM pricing
                'is_free': not segment.get('fees'),  # No fees means free/owned
                'has_coverage_data': coverage is not None,
                'has_pricing_data': cpm is not None,
                'catalog_access': 'personalized',  # IX segments are account-specific
                'platform': 'index-exchange',
                'account_id': account_id,
                'raw_data': segment  # Store original data for reference
            }
            normalized.append(normalized_segment)
        
        return normalized
    
    def _map_segment_type(self, segment: Dict) -> str:
        """Map Index Exchange segment types to our taxonomy."""
        # Index Exchange segment types - this may need adjustment based on actual API response
        segment_type = segment.get('type', segment.get('segmentType', ''))
        category = segment.get('category', segment.get('segmentCategory', ''))
        
        # Map common categories
        if 'automotive' in category.lower() or 'auto' in category.lower():
            return 'automotive'
        elif 'financial' in category.lower() or 'finance' in category.lower():
            return 'financial'
        elif 'retail' in category.lower() or 'shopping' in category.lower():
            return 'retail'
        elif 'travel' in category.lower():
            return 'travel'
        else:
            return 'behavioral'  # Default fallback
    
    def _estimate_coverage(self, segment: Dict) -> Optional[float]:
        """Get coverage from Index Exchange data if available."""
        # Check for actual reach/coverage data in the response
        # Look for fields like userCount, reach, coverage, size, etc.
        for field in ['userCount', 'reach', 'coverage', 'size', 'audienceSize']:
            if field in segment and segment[field]:
                raw_count = segment[field]
                # Convert to percentage assuming US online population ~250M
                if isinstance(raw_count, (int, float)) and raw_count > 0:
                    coverage_pct = (raw_count / 250_000_000) * 100
                    return round(min(coverage_pct, 50.0), 1)  # Cap at 50%
        
        # No data available - return None instead of estimating
        return None
    
    def _extract_cpm_from_fees(self, segment: Dict) -> Optional[float]:
        """Extract CPM from Index Exchange fees structure if available."""
        fees = segment.get('fees', [])
        
        if not fees:
            # No fees means it's free or we're the provider
            return 0.0
        
        # Find the applicable fee
        # In production, you'd match based on targets, but for now take the first fee
        if isinstance(fees, list) and len(fees) > 0:
            first_fee = fees[0]
            fee_details = first_fee.get('fee', {})
            
            # Look for CPM in fee structure
            # Note: The exact field name may vary - adjust based on actual API response
            if 'cpm' in fee_details:
                return float(fee_details['cpm'])
            elif 'price' in fee_details:
                return float(fee_details['price'])
            elif 'rate' in fee_details:
                return float(fee_details['rate'])
        
        return None
    
    def _estimate_cpm(self, segment: Dict) -> Optional[float]:
        """Get CPM from Index Exchange fees if available."""
        # Try to get actual CPM from fees
        actual_cpm = self._extract_cpm_from_fees(segment)
        if actual_cpm is not None:
            return actual_cpm
        
        # No pricing data available
        return None
    
    def activate_segment(self, segment_id: str, account_id: str, activation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Activate a segment on Index Exchange."""
        # For Index Exchange, activation typically means making the segment available for targeting
        # This would integrate with their campaign management API
        
        # For now, simulate activation
        return {
            'platform_activation_id': f"ix_activation_{segment_id}_{account_id}",
            'status': 'activating',
            'estimated_duration_minutes': 15,
            'activation_started_at': datetime.now().isoformat()
        }
    
    def check_segment_status(self, segment_id: str, account_id: str) -> Dict[str, Any]:
        """Check the status of a segment on Index Exchange."""
        # This would query Index Exchange for segment status
        # For now, simulate that segments are available after a short delay
        
        return {
            'status': 'deployed',
            'is_live': True,
            'deployed_at': datetime.now().isoformat(),
            'platform_segment_id': segment_id
        }