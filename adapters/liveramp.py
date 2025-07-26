"""LiveRamp Data Marketplace platform adapter."""

import requests
import json
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import PlatformAdapter


class LiveRampAdapter(PlatformAdapter):
    """Adapter for LiveRamp Data Marketplace API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.liveramp.com')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.auth_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("LiveRamp adapter requires client_id and client_secret in config")
    
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with LiveRamp using OAuth2 client credentials flow."""
        # Check if we have a valid token in cache
        if self._is_token_valid():
            return {
                'access_token': self.auth_token,
                'expires_at': self.token_expires_at
            }
        
        # Get new token
        auth_url = f"{self.base_url}/v2/tokens/marketplace"
        
        # Create basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(auth_url, headers=headers, data=data)
        
        if response.status_code != 200:
            raise Exception(f"LiveRamp authentication failed: {response.status_code} {response.text}")
        
        token_data = response.json()
        self.auth_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
        self.token_expires_at = datetime.now().timestamp() + expires_in
        
        return {
            'access_token': self.auth_token,
            'expires_at': self.token_expires_at
        }
    
    def _is_token_valid(self) -> bool:
        """Check if current auth token is still valid."""
        if not self.auth_token or not self.token_expires_at:
            return False
        
        # Add 5 minute buffer before expiration
        return datetime.now().timestamp() < (self.token_expires_at - 300)
    
    def get_segments(self, account_id: str, principal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch audience segments from LiveRamp Data Marketplace."""
        # Validate principal access to account
        if principal_id and not self._validate_principal_access(principal_id, account_id):
            raise ValueError(f"Principal '{principal_id}' does not have access to account '{account_id}'")
        
        # Check cache first
        cache_key = f"liveramp_segments_{account_id}"
        cached_segments = self._get_from_cache(cache_key)
        if cached_segments:
            return cached_segments
        
        # Ensure we have valid authentication
        self.authenticate()
        
        # Fetch segments from LiveRamp API
        segments_url = f"{self.base_url}/v3/segments"
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Accept': 'application/json'
        }
        
        # API supports many filters - start with basics
        params = {
            'limit': 100,  # Max allowed per page
            'offset': 0,
            'sort': 'name',
            'order': 'asc'
        }
        
        all_segments = []
        
        # Handle pagination
        while True:
            response = requests.get(segments_url, headers=headers, params=params)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch segments: {response.status_code} {response.text}")
            
            data = response.json()
            segments = data.get('segments', [])
            all_segments.extend(segments)
            
            # Check if there are more pages
            total = data.get('total', 0)
            if len(all_segments) >= total:
                break
            
            params['offset'] += params['limit']
        
        # Normalize segments to our format
        normalized_segments = self._normalize_segments(all_segments, account_id)
        
        # Cache the results
        self._set_cache(cache_key, normalized_segments)
        
        return normalized_segments
    
    def _normalize_segments(self, raw_segments: List[Dict], account_id: str) -> List[Dict[str, Any]]:
        """Normalize LiveRamp segments to our internal format."""
        normalized = []
        
        for segment in raw_segments:
            # Extract relevant fields from LiveRamp API
            segment_id = segment.get('id')
            segment_name = segment.get('name', f'LiveRamp Segment {segment_id}')
            description = segment.get('description', '')
            
            # Get seller information
            seller_info = segment.get('seller', {})
            seller_name = seller_info.get('name', 'Unknown Seller')
            
            # Get pricing information
            pricing_info = segment.get('pricing', {})
            cpm = None
            is_free = False
            
            # LiveRamp uses different pricing models
            if pricing_info.get('type') == 'CPM':
                cpm = pricing_info.get('value', 0.0)
                is_free = cpm == 0
            elif pricing_info.get('type') == 'FREE':
                cpm = 0.0
                is_free = True
            
            # Get audience size/reach
            audience_info = segment.get('audience', {})
            reach = audience_info.get('reach', {})
            
            # LiveRamp provides reach as a number, convert to percentage
            coverage = None
            if reach.get('value'):
                # Assuming US population for percentage calculation
                coverage = (reach.get('value', 0) / 250_000_000) * 100
                coverage = round(min(coverage, 50.0), 1)  # Cap at 50%
            
            # Get categories
            categories = segment.get('categories', [])
            category_names = [cat.get('name', '') for cat in categories]
            
            normalized_segment = {
                'id': f"liveramp_{account_id}_{segment_id}",
                'platform_segment_id': str(segment_id),
                'name': segment_name,
                'description': description or f"LiveRamp segment from {seller_name}",
                'audience_type': 'marketplace',  # LiveRamp is a data marketplace
                'data_provider': f"LiveRamp ({seller_name})",
                'coverage_percentage': coverage,
                'base_cpm': cpm if cpm is not None else 0.0,
                'revenue_share_percentage': 0.0,  # LiveRamp typically uses CPM pricing
                'is_free': is_free,
                'has_coverage_data': coverage is not None,
                'has_pricing_data': cpm is not None,
                'catalog_access': 'personalized',  # Account-specific access
                'platform': 'liveramp',
                'account_id': account_id,
                'categories': category_names,
                'raw_data': segment  # Store original data for reference
            }
            normalized.append(normalized_segment)
        
        return normalized
    
    def activate_segment(self, segment_id: str, account_id: str, activation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Activate a segment on LiveRamp Data Marketplace."""
        # Ensure we have valid authentication
        self.authenticate()
        
        # LiveRamp activation endpoint
        activation_url = f"{self.base_url}/v3/requestedSegments"
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Build activation request
        # LiveRamp requires specific fields for activation
        activation_data = {
            'segmentId': segment_id,
            'name': activation_config.get('name', f'Activation_{segment_id}'),
            'description': activation_config.get('description', 'Activated via Audience Agent'),
            'destinations': activation_config.get('destinations', [])  # LiveRamp specific destinations
        }
        
        response = requests.post(activation_url, headers=headers, json=activation_data)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to activate segment: {response.status_code} {response.text}")
        
        activation_response = response.json()
        
        return {
            'platform_activation_id': activation_response.get('id'),
            'status': 'activating',
            'estimated_duration_minutes': 30,  # LiveRamp typically takes 15-30 minutes
            'activation_started_at': datetime.now().isoformat(),
            'raw_response': activation_response
        }
    
    def check_segment_status(self, segment_id: str, account_id: str) -> Dict[str, Any]:
        """Check the status of a segment activation on LiveRamp."""
        # Ensure we have valid authentication
        self.authenticate()
        
        # LiveRamp status endpoint
        status_url = f"{self.base_url}/v3/requestedSegments/{segment_id}"
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Accept': 'application/json'
        }
        
        response = requests.get(status_url, headers=headers)
        
        if response.status_code == 404:
            return {
                'status': 'not_found',
                'is_live': False,
                'error_message': 'Segment activation not found'
            }
        elif response.status_code != 200:
            raise Exception(f"Failed to check segment status: {response.status_code} {response.text}")
        
        status_data = response.json()
        
        # Map LiveRamp status to our status
        liveramp_status = status_data.get('status', '').upper()
        
        if liveramp_status == 'ACTIVE':
            return {
                'status': 'deployed',
                'is_live': True,
                'deployed_at': status_data.get('activatedAt', datetime.now().isoformat()),
                'platform_segment_id': segment_id
            }
        elif liveramp_status in ['PENDING', 'PROCESSING']:
            return {
                'status': 'activating',
                'is_live': False,
                'platform_segment_id': segment_id
            }
        elif liveramp_status in ['FAILED', 'ERROR']:
            return {
                'status': 'failed',
                'is_live': False,
                'error_message': status_data.get('errorMessage', 'Activation failed'),
                'platform_segment_id': segment_id
            }
        else:
            return {
                'status': 'unknown',
                'is_live': False,
                'platform_segment_id': segment_id,
                'raw_status': liveramp_status
            }