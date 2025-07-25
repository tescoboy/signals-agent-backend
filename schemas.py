"""Pydantic models for the Audience Activation Protocol."""

from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# --- Core Protocol Models ---

class PlatformDeployment(BaseModel):
    """Single platform deployment information."""
    platform: str
    account: Optional[str] = None
    is_live: bool
    scope: Literal["platform-wide", "account-specific"]
    decisioning_platform_segment_id: Optional[str] = None
    estimated_activation_duration_minutes: Optional[int] = None


class PricingModel(BaseModel):
    """Pricing information for an audience."""
    cpm: Optional[float] = None
    revenue_share_percentage: Optional[float] = None
    currency: str = "USD"


class AudienceResponse(BaseModel):
    """Single audience in get_audiences response."""
    audience_agent_segment_id: str
    name: str
    description: str
    audience_type: Literal["private", "marketplace"]
    data_provider: str
    coverage_percentage: Optional[float] = None
    deployments: List[PlatformDeployment]
    pricing: PricingModel
    has_coverage_data: Optional[bool] = None
    has_pricing_data: Optional[bool] = None


# --- Request Models ---

class DeliverySpecification(BaseModel):
    """Platform delivery specification."""
    platforms: Union[List[Dict[str, Any]], Literal["all"]]
    countries: List[str] = ["US"]


class AudienceFilters(BaseModel):
    """Filters for audience discovery."""
    catalog_types: Optional[List[Literal["private", "marketplace"]]] = None
    data_providers: Optional[List[str]] = None
    max_cpm: Optional[float] = None
    min_coverage_percentage: Optional[float] = None


class GetAudiencesRequest(BaseModel):
    """Request for discovering audiences."""
    audience_spec: str
    deliver_to: DeliverySpecification
    filters: Optional[AudienceFilters] = None
    max_results: Optional[int] = 10


class CustomSegmentProposal(BaseModel):
    """AI-generated custom segment proposal."""
    proposed_name: str
    description: str
    target_audience: str
    estimated_coverage_percentage: float
    estimated_cpm: float
    creation_rationale: str
    custom_segment_id: Optional[str] = None  # ID for activation


class GetAudiencesResponse(BaseModel):
    """Response from get_audiences."""
    audiences: List[AudienceResponse]
    custom_segment_proposals: Optional[List[CustomSegmentProposal]] = None


class ActivateAudienceRequest(BaseModel):
    """Request to activate an audience."""
    audience_agent_segment_id: str
    platform: str
    account: Optional[str] = None


class ActivateAudienceResponse(BaseModel):
    """Response from activate_audience."""
    decisioning_platform_segment_id: str
    estimated_activation_duration_minutes: int


class CheckAudienceStatusRequest(BaseModel):
    """Request to check audience status."""
    audience_agent_segment_id: str
    decisioning_platform: str
    account: Optional[str] = None


class CheckAudienceStatusResponse(BaseModel):
    """Response from check_audience_status."""
    status: Literal["deployed", "activating", "failed", "not_found"]
    deployed_at: Optional[datetime] = None
    error_message: Optional[str] = None




# --- Database Models ---

class AudienceSegment(BaseModel):
    """Internal audience segment model."""
    id: str
    name: str
    description: str
    data_provider: str
    coverage_percentage: float
    audience_type: Literal["private", "marketplace"]
    catalog_access: Literal["public", "personalized", "private"]
    base_cpm: float
    revenue_share_percentage: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class PlatformDeploymentRecord(BaseModel):
    """Database record for platform deployments."""
    audience_agent_segment_id: str
    platform: str
    account: Optional[str] = None
    decisioning_platform_segment_id: Optional[str] = None
    scope: Literal["platform-wide", "account-specific"]
    is_live: bool
    deployed_at: Optional[datetime] = None
    estimated_activation_duration_minutes: int = 60


# --- Error Models ---

class AudienceError(BaseModel):
    """Error response model."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Error codes as defined in the specification
AUDIENCE_AGENT_SEGMENT_NOT_FOUND = "AUDIENCE_AGENT_SEGMENT_NOT_FOUND"
ACTIVATION_FAILED = "ACTIVATION_FAILED"
ALREADY_ACTIVATED = "ALREADY_ACTIVATED"
DEPLOYMENT_UNAUTHORIZED = "DEPLOYMENT_UNAUTHORIZED"
INVALID_PRICING_MODEL = "INVALID_PRICING_MODEL"
AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
AGENT_ACCESS_DENIED = "AGENT_ACCESS_DENIED"