"""Main MCP server implementation for the Audience Activation Protocol."""

import json
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from fastmcp import FastMCP
from rich.console import Console

from database import init_db
from schemas import *
from adapters.manager import AdapterManager
from config_loader import load_config


# In-memory storage for custom segments and activations
custom_segments: Dict[str, Dict] = {}
segment_activations: Dict[str, Dict] = {}


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect('audience_agent.db')
    conn.row_factory = sqlite3.Row
    return conn


def rank_audiences_with_ai(audience_spec: str, segments: List[Dict], max_results: int = 10) -> List[Dict]:
    """Use Gemini to intelligently rank audience segments based on the specification."""
    if not segments:
        return []
    
    # Prepare segment data for AI analysis
    segment_data = []
    for segment in segments:
        segment_data.append({
            "id": segment["id"],
            "name": segment["name"], 
            "description": segment["description"],
            "coverage_percentage": segment["coverage_percentage"],
            "cpm": segment["base_cpm"]
        })
    
    prompt = f"""
    You are an expert audience targeting analyst. A client has requested audiences for: "{audience_spec}"
    
    Here are available audience segments from Peer39:
    {json.dumps(segment_data, indent=2)}
    
    Please:
    1. Rank these segments by relevance to the client's request (most relevant first)
    2. Select the top {max_results} most relevant segments
    3. For each selected segment, provide a brief explanation of why it matches the request
    
    Return your response as a JSON array with this structure:
    [
      {{
        "segment_id": "segment_id",
        "relevance_score": 0.95,
        "match_reason": "Brief explanation of why this segment matches the request"
      }}
    ]
    
    Only include segments that have at least some relevance. If none are relevant, return an empty array.
    """
    
    try:
        response = model.generate_content(prompt)
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        ai_rankings = json.loads(clean_json_str)
        
        # Reorder segments based on AI ranking
        ranked_segments = []
        for ranking in ai_rankings:
            segment_id = ranking.get("segment_id")
            match_reason = ranking.get("match_reason", "Relevant to your query")
            
            # Find the matching segment
            for segment in segments:
                if segment["id"] == segment_id:
                    # Add the match reason to the segment
                    segment_copy = segment.copy()
                    segment_copy["match_reason"] = match_reason
                    ranked_segments.append(segment_copy)
                    break
        
        return ranked_segments
        
    except Exception as e:
        console.print(f"[yellow]AI ranking failed ({e}), using basic text matching[/yellow]")
        # Fallback to basic text matching
        return segments[:max_results]


def generate_custom_segment_proposals(audience_spec: str, existing_segments: List[Dict]) -> List[Dict]:
    """Use Gemini to propose custom segments that could be created for this query."""
    
    existing_names = [seg["name"] for seg in existing_segments]
    
    prompt = f"""
    You are a contextual audience targeting expert. A client is looking for: "{audience_spec}"
    
    We found these existing Peer39 segments:
    {json.dumps(existing_names, indent=2)}
    
    Based on the client's request, propose 2-3 NEW custom contextual segments that Peer39 could create to better serve this targeting need. These should be segments that don't currently exist but would be valuable.
    
    For each proposal, consider:
    - What specific contextual signals could be used
    - What makes this segment unique from existing ones
    - Why an advertiser would pay a premium for this targeting
    
    Return your response as a JSON array:
    [
      {{
        "proposed_name": "Specific segment name",
        "description": "Detailed description of what content/context this targets",
        "target_audience": "Who this reaches (demographics/psychographics)",
        "estimated_coverage_percentage": 2.5,
        "estimated_cpm": 6.50,
        "creation_rationale": "Why this segment would be valuable and what signals would be used"
      }}
    ]
    
    Focus on high-value, specific segments that would command premium pricing.
    """
    
    try:
        response = model.generate_content(prompt)
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        proposals = json.loads(clean_json_str)
        return proposals
        
    except Exception as e:
        console.print(f"[yellow]Custom segment proposal generation failed ({e})[/yellow]")
        return []


# --- Application Setup ---
config = load_config()
init_db()

# Initialize Gemini
genai.configure(api_key=config.get("gemini_api_key", "your-api-key-here"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize platform adapters
adapter_manager = AdapterManager(config)

mcp = FastMCP(name="AudienceActivationAgent")
console = Console()


# --- MCP Tools ---

@mcp.tool
def get_audience_examples() -> Dict[str, Any]:
    """
    Get examples of how to use the audience discovery tools.
    
    Returns common usage patterns and platform configurations.
    """
    return {
        "description": "Examples for using the Audience Activation Protocol",
        "get_audiences_examples": [
            {
                "description": "Search all platforms for luxury audiences",
                "request": {
                    "audience_spec": "luxury car buyers in California",
                    "deliver_to": {
                        "platforms": "all",
                        "countries": ["US"]
                    }
                }
            },
            {
                "description": "Search specific platforms with account",
                "request": {
                    "audience_spec": "parents with young children",
                    "deliver_to": {
                        "platforms": [
                            {"platform": "the-trade-desk"},
                            {"platform": "index-exchange", "account": "1489997"}
                        ],
                        "countries": ["US", "UK"]
                    },
                    "principal_id": "acme_corp"
                }
            },
            {
                "description": "Search with price filters",
                "request": {
                    "audience_spec": "budget-conscious travelers",
                    "deliver_to": {
                        "platforms": "all",
                        "countries": ["US"]
                    },
                    "filters": {
                        "max_cpm": 5.0,
                        "min_coverage_percentage": 10.0
                    }
                }
            }
        ],
        "available_platforms": [
            "the-trade-desk",
            "index-exchange",
            "openx",
            "pubmatic",
            "google-dv360",
            "amazon-dsp"
        ],
        "principal_ids": [
            "acme_corp (personalized catalog)",
            "premium_partner (personalized catalog)",
            "enterprise_client (private catalog)"
        ]
    }


@mcp.tool
def get_audiences(
    audience_spec: str,
    deliver_to: DeliverySpecification,
    filters: Optional[AudienceFilters] = None,
    max_results: Optional[int] = 10,
    principal_id: Optional[str] = None
) -> GetAudiencesResponse:
    """
    Discover relevant audiences based on a marketing specification.
    
    This tool uses AI to match your natural language audience description with available segments
    across multiple decisioning platforms.
    
    Args:
        audience_spec: Natural language description of your target audience
                      Examples: "luxury car buyers", "parents with young children", 
                                "high-income travelers"
        
        deliver_to: Where to search for audiences
                    - Set platforms to "all" to search across all platforms
                    - Or specify specific platforms like:
                      {"platforms": [{"platform": "the-trade-desk"}, 
                                     {"platform": "index-exchange", "account": "1489997"}]}
        
        filters: Optional filters to refine results (max_cpm, min_coverage, etc.)
        
        max_results: Number of audiences to return (1-100, default 10)
        
        principal_id: Your account ID for accessing private catalogs and custom pricing
                      Examples: "acme_corp", "agency_123"
    
    Returns:
        List of matching audiences with deployment status, pricing, and AI-generated
        match explanations. Also includes custom segment proposals when relevant.
    """
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Determine catalog access based on principal
    principal_access_level = 'public'  # Default
    if principal_id:
        cursor.execute("SELECT access_level FROM principals WHERE principal_id = ?", (principal_id,))
        principal_row = cursor.fetchone()
        if principal_row:
            principal_access_level = principal_row['access_level']
    
    # Build query based on principal access level
    if principal_access_level == 'public':
        catalog_filter = "catalog_access = 'public'"
    elif principal_access_level == 'personalized':
        catalog_filter = "catalog_access IN ('public', 'personalized')"
    else:  # private
        catalog_filter = "catalog_access IN ('public', 'personalized', 'private')"
    
    query = f"""
        SELECT * FROM audience_segments 
        WHERE {catalog_filter}
    """
    params = []
    
    if filters:
        if filters.catalog_types:
            placeholders = ','.join('?' * len(filters.catalog_types))
            query += f" AND audience_type IN ({placeholders})"
            params.extend(filters.catalog_types)
        
        if filters.data_providers:
            placeholders = ','.join('?' * len(filters.data_providers))
            query += f" AND data_provider IN ({placeholders})"
            params.extend(filters.data_providers)
        
        if filters.max_cpm:
            query += " AND base_cpm <= ?"
            params.append(filters.max_cpm)
        
        if filters.min_coverage_percentage:
            query += " AND coverage_percentage >= ?"
            params.append(filters.min_coverage_percentage)
    
    # Apply flexible text matching on name and description
    if audience_spec:
        # Split the spec into individual words for better matching
        words = audience_spec.lower().split()
        word_conditions = []
        for word in words:
            word_conditions.append("(LOWER(name) LIKE ? OR LOWER(description) LIKE ?)")
            word_pattern = f"%{word}%"
            params.extend([word_pattern, word_pattern])
        
        if word_conditions:
            # Use OR to match any of the words
            query += " AND (" + " OR ".join(word_conditions) + ")"
    
    query += f" ORDER BY coverage_percentage DESC LIMIT ?"
    params.append(max_results or 10)
    
    cursor.execute(query, params)
    db_segments = [dict(row) for row in cursor.fetchall()]
    
    # Get segments from platform adapters
    platform_segments = []
    try:
        platform_segments = adapter_manager.get_all_segments(
            deliver_to.model_dump(), 
            principal_id
        )
        if platform_segments:
            console.print(f"[dim]Found {len(platform_segments)} segments from platform APIs[/dim]")
    except Exception as e:
        console.print(f"[yellow]Platform adapter error: {e}[/yellow]")
    
    # Combine database and platform segments
    all_segments = db_segments + platform_segments
    
    # Use AI to rank segments by relevance to the audience spec
    ranked_segments = rank_audiences_with_ai(audience_spec, all_segments, max_results or 10)
    
    audiences = []
    for segment in ranked_segments:
        platform_deployments = []
        
        # Handle platform adapter segments differently than database segments
        if segment.get('platform'):
            # This is a platform adapter segment
            platform_name = segment['platform']
            account_id = segment.get('account_id')
            
            # Check if this platform was requested
            if isinstance(deliver_to.platforms, str) and deliver_to.platforms == "all":
                # Include all platforms
                include_platform = True
            else:
                # Check if this platform is in the requested list
                requested_platforms = set()
                for p in deliver_to.platforms:
                    if hasattr(p, 'platform'):  # PlatformSpecification object
                        requested_platforms.add(p.platform)
                    elif isinstance(p, dict):  # Legacy dict format
                        requested_platforms.add(p.get('platform'))
                    else:  # String format
                        requested_platforms.add(p)
                include_platform = platform_name in requested_platforms
            
            if include_platform:
                # Create a deployment record for the platform segment
                platform_deployments = [PlatformDeployment(
                    audience_agent_segment_id=segment['id'],
                    platform=platform_name,
                    account=account_id,
                    decisioning_platform_segment_id=segment.get('platform_segment_id', segment['id']),
                    scope="account-specific" if account_id else "platform-wide",
                    is_live=True,  # Platform adapter segments are assumed live
                    deployed_at=datetime.now().isoformat(),
                    estimated_activation_duration_minutes=15
                )]
        else:
            # This is a database segment - get platform deployments as before
            cursor.execute("""
                SELECT * FROM platform_deployments 
                WHERE audience_agent_segment_id = ?
            """, (segment['id'],))
            deployments = [dict(row) for row in cursor.fetchall()]
            
            # Filter deployments based on requested platforms
            if isinstance(deliver_to.platforms, str) and deliver_to.platforms == "all":
                # Return all deployments
                platform_deployments = [PlatformDeployment(**dep) for dep in deployments]
            else:
                # Filter deployments by requested platforms
                requested_platforms = set()
                for p in deliver_to.platforms:
                    if hasattr(p, 'platform'):  # PlatformSpecification object
                        requested_platforms.add(p.platform)
                    elif isinstance(p, dict):  # Legacy dict format
                        requested_platforms.add(p.get('platform'))
                    else:  # String format
                        requested_platforms.add(p)
                platform_deployments = []
                
                for dep in deployments:
                    if dep['platform'] in requested_platforms:
                        platform_deployments.append(PlatformDeployment(**dep))
        
        if platform_deployments:
            # Check for custom pricing for this principal
            cpm = segment['base_cpm']
            if principal_id and not segment.get('platform'):
                # Only check database for custom pricing on database segments
                cursor.execute("""
                    SELECT custom_cpm FROM principal_segment_access 
                    WHERE principal_id = ? AND audience_agent_segment_id = ? AND custom_cpm IS NOT NULL
                """, (principal_id, segment['id']))
                custom_pricing = cursor.fetchone()
                if custom_pricing:
                    cpm = custom_pricing['custom_cpm']
            
            audience = AudienceResponse(
                audience_agent_segment_id=segment['id'],
                name=segment['name'],
                description=segment['description'],
                audience_type=segment['audience_type'],
                data_provider=segment['data_provider'],
                coverage_percentage=segment['coverage_percentage'],
                deployments=platform_deployments,
                pricing=PricingModel(
                    cpm=cpm,
                    revenue_share_percentage=segment['revenue_share_percentage']
                ),
                has_coverage_data=segment.get('has_coverage_data', True),  # Database segments have coverage
                has_pricing_data=segment.get('has_pricing_data', True)  # Database segments have pricing
            )
            audiences.append(audience)
    
    # Generate custom segment proposals
    custom_proposals = []
    if audiences:  # Only generate proposals if we found some existing segments
        proposal_data = generate_custom_segment_proposals(audience_spec, ranked_segments)
        for proposal in proposal_data:
            # Generate unique ID for custom segment
            custom_id = f"custom_{len(custom_segments) + 1}_{hash(proposal['proposed_name']) % 10000}"
            
            # Store in memory for later activation
            custom_segments[custom_id] = {
                "id": custom_id,
                "name": proposal['proposed_name'],
                "description": f"Custom segment: {proposal['target_audience']}",
                "audience_type": "custom",
                "data_provider": "Custom AI Generated",
                "coverage_percentage": proposal['estimated_coverage_percentage'],
                "base_cpm": proposal['estimated_cpm'],
                "revenue_share_percentage": 0.0,
                "catalog_access": "personalized",
                "creation_rationale": proposal['creation_rationale'],
                "created_at": datetime.now().isoformat()
            }
            
            # Add the custom ID to the proposal
            proposal_with_id = CustomSegmentProposal(
                **proposal,
                custom_segment_id=custom_id
            )
            custom_proposals.append(proposal_with_id)
    
    conn.close()
    return GetAudiencesResponse(
        audiences=audiences,
        custom_segment_proposals=custom_proposals if custom_proposals else None
    )


@mcp.tool
def activate_audience(
    audience_agent_segment_id: str,
    platform: str,
    account: Optional[str] = None,
    principal_id: Optional[str] = None
) -> ActivateAudienceResponse:
    """Activate an audience for use on a specific platform/account."""
    
    # Check if this is a custom segment
    if audience_agent_segment_id.startswith("custom_"):
        if audience_agent_segment_id not in custom_segments:
            raise ValueError(f"Custom segment '{audience_agent_segment_id}' not found")
        
        segment = custom_segments[audience_agent_segment_id]
        
        # Check if already activated
        activation_key = f"{audience_agent_segment_id}_{platform}_{account or 'default'}"
        if activation_key in segment_activations:
            existing = segment_activations[activation_key]
            if existing.get('status') == 'deployed':
                raise ValueError("Custom segment already activated for this platform/account")
        
        # Generate platform segment ID
        account_suffix = f"_{account}" if account else ""
        decisioning_platform_segment_id = f"{platform}_{audience_agent_segment_id}{account_suffix}"
        
        # Simulate custom segment creation process
        activation_duration = 120  # Custom segments take longer to create
        
        # Store activation record
        segment_activations[activation_key] = {
            "audience_agent_segment_id": audience_agent_segment_id,
            "platform": platform,
            "account": account,
            "decisioning_platform_segment_id": decisioning_platform_segment_id,
            "status": "activating",
            "activation_started_at": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(minutes=activation_duration)).isoformat()
        }
        
        console.print(f"[bold cyan]Creating and activating custom segment '{segment['name']}' on {platform}[/bold cyan]")
        console.print(f"[dim]This involves building the segment from scratch, estimated duration: {activation_duration} minutes[/dim]")
        
        return ActivateAudienceResponse(
            decisioning_platform_segment_id=decisioning_platform_segment_id,
            estimated_activation_duration_minutes=activation_duration
        )
    
    # Handle regular database segments
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if segment exists and principal has access
    cursor.execute(
        "SELECT * FROM audience_segments WHERE id = ?",
        (audience_agent_segment_id,)
    )
    segment = cursor.fetchone()
    if not segment:
        raise ValueError(f"Audience segment '{audience_agent_segment_id}' not found")
    
    # Check principal access if specified
    if principal_id:
        cursor.execute("SELECT access_level FROM principals WHERE principal_id = ?", (principal_id,))
        principal_row = cursor.fetchone()
        if principal_row:
            principal_access_level = principal_row['access_level']
            
            # Check if principal can access this segment
            if segment['catalog_access'] == 'private' and principal_access_level != 'private':
                raise ValueError(f"Principal '{principal_id}' does not have access to private segment '{audience_agent_segment_id}'")
            elif segment['catalog_access'] == 'personalized' and principal_access_level == 'public':
                raise ValueError(f"Principal '{principal_id}' does not have access to personalized segment '{audience_agent_segment_id}'")
    
    # Check if already activated
    cursor.execute("""
        SELECT * FROM platform_deployments 
        WHERE audience_agent_segment_id = ? AND platform = ? AND account IS ?
    """, (audience_agent_segment_id, platform, account))
    
    existing = cursor.fetchone()
    if existing and existing['is_live']:
        raise ValueError("Audience already activated for this platform/account")
    
    # Generate platform segment ID
    account_suffix = f"_{account}" if account else ""
    decisioning_platform_segment_id = f"{platform}_{audience_agent_segment_id}{account_suffix}"
    
    # Create or update deployment record
    scope = "account-specific" if account else "platform-wide"
    activation_duration = config.get('deployment', {}).get('default_activation_duration_minutes', 60)
    
    if existing:
        # Update existing record
        cursor.execute("""
            UPDATE platform_deployments 
            SET decisioning_platform_segment_id = ?, is_live = 0, 
                estimated_activation_duration_minutes = ?
            WHERE audience_agent_segment_id = ? AND platform = ? AND account IS ?
        """, (decisioning_platform_segment_id, activation_duration, 
              audience_agent_segment_id, platform, account))
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO platform_deployments 
            (audience_agent_segment_id, platform, account, decisioning_platform_segment_id, 
             scope, is_live, estimated_activation_duration_minutes)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (audience_agent_segment_id, platform, account, decisioning_platform_segment_id,
              scope, activation_duration))
    
    conn.commit()
    conn.close()
    
    console.print(f"[bold green]Activating audience {audience_agent_segment_id} on {platform}[/bold green]")
    
    return ActivateAudienceResponse(
        decisioning_platform_segment_id=decisioning_platform_segment_id,
        estimated_activation_duration_minutes=activation_duration
    )


@mcp.tool
def check_audience_status(
    audience_agent_segment_id: str,
    decisioning_platform: str,
    account: Optional[str] = None,
    principal_id: Optional[str] = None
) -> CheckAudienceStatusResponse:
    """Check the deployment status of an audience on a decisioning platform."""
    
    # Check if this is a custom segment
    if audience_agent_segment_id.startswith("custom_"):
        activation_key = f"{audience_agent_segment_id}_{decisioning_platform}_{account or 'default'}"
        
        if activation_key not in segment_activations:
            return CheckAudienceStatusResponse(status="not_found")
        
        activation = segment_activations[activation_key]
        
        if activation['status'] == 'deployed':
            return CheckAudienceStatusResponse(
                status="deployed",
                deployed_at=datetime.fromisoformat(activation.get('deployed_at', activation['activation_started_at']))
            )
        elif activation['status'] == 'activating':
            # Check if enough time has passed to complete the activation
            estimated_completion = datetime.fromisoformat(activation['estimated_completion'])
            if datetime.now() >= estimated_completion:
                # Mark as deployed
                activation['status'] = 'deployed'
                activation['deployed_at'] = datetime.now().isoformat()
                segment_activations[activation_key] = activation
                
                console.print(f"[bold green]Custom segment '{audience_agent_segment_id}' is now live on {decisioning_platform}[/bold green]")
                
                return CheckAudienceStatusResponse(
                    status="deployed",
                    deployed_at=datetime.now()
                )
            else:
                # Still activating
                return CheckAudienceStatusResponse(status="activating")
        
        return CheckAudienceStatusResponse(status="failed")
    
    # Handle regular database segments
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check principal access if specified
    if principal_id:
        cursor.execute("SELECT * FROM audience_segments WHERE id = ?", (audience_agent_segment_id,))
        segment = cursor.fetchone()
        if segment:
            cursor.execute("SELECT access_level FROM principals WHERE principal_id = ?", (principal_id,))
            principal_row = cursor.fetchone()
            if principal_row:
                principal_access_level = principal_row['access_level']
                
                # Check if principal can access this segment
                if segment['catalog_access'] == 'private' and principal_access_level != 'private':
                    return CheckAudienceStatusResponse(status="not_found")  # Don't reveal existence
                elif segment['catalog_access'] == 'personalized' and principal_access_level == 'public':
                    return CheckAudienceStatusResponse(status="not_found")  # Don't reveal existence
    
    cursor.execute("""
        SELECT * FROM platform_deployments 
        WHERE audience_agent_segment_id = ? AND platform = ? AND account IS ?
    """, (audience_agent_segment_id, decisioning_platform, account))
    
    deployment = cursor.fetchone()
    
    if not deployment:
        conn.close()
        return CheckAudienceStatusResponse(status="not_found")
    
    if deployment['is_live']:
        conn.close()
        return CheckAudienceStatusResponse(
            status="deployed",
            deployed_at=datetime.fromisoformat(deployment['deployed_at']) if deployment['deployed_at'] else None
        )
    else:
        # For demo purposes, immediately mark as deployed
        cursor.execute("""
            UPDATE platform_deployments 
            SET is_live = 1, deployed_at = ?
            WHERE audience_agent_segment_id = ? AND platform = ? AND account IS ?
        """, (datetime.now().isoformat(), audience_agent_segment_id, decisioning_platform, account))
        conn.commit()
        conn.close()
        
        return CheckAudienceStatusResponse(
            status="deployed",
            deployed_at=datetime.now()
        )




if __name__ == "__main__":
    mcp.run()