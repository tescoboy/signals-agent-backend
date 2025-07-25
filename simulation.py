"""End-to-end simulation of the Audience Activation Protocol."""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from main import mcp
from schemas import *


console = Console()


def print_step(step_number: int, title: str, description: str):
    """Print a simulation step header."""
    console.print(f"\n[bold blue]Step {step_number}: {title}[/bold blue]")
    console.print(f"[dim]{description}[/dim]")


def print_response(title: str, data: Any):
    """Print a formatted response."""
    console.print(Panel(
        json.dumps(data, indent=2, default=str),
        title=title,
        border_style="green"
    ))


def run_simulation():
    """Run the complete audience activation simulation."""
    
    console.print("[bold cyan]🎯 Audience Activation Protocol Simulation[/bold cyan]")
    console.print("Demonstrating the complete audience discovery and activation workflow\n")
    
    # --- Step 1: Multi-Platform Discovery ---
    print_step(1, "Multi-Platform Audience Discovery",
               "Discover luxury automotive audiences across multiple SSPs")
    
    multi_platform_request = GetAudiencesRequest(
        audience_spec="Premium automotive intenders in major urban markets",
        deliver_to=DeliverySpecification(
            platforms=[
                {"platform": "index-exchange", "account": "agency-123-ix"},
                {"platform": "openx"},
                {"platform": "pubmatic", "account": "brand-456-pm"}
            ],
            countries=["US", "CA"]
        ),
        filters=AudienceFilters(
            catalog_types=["marketplace"],
            max_cpm=5.0,
            min_coverage_percentage=10
        ),
        max_results=5
    )
    
    response = mcp.call_tool("get_audiences", **multi_platform_request.model_dump())
    print_response("Multi-Platform Discovery Response", response)
    
    # --- Step 2: All Platforms Discovery ---
    print_step(2, "All Platforms Discovery",
               "Discover contextual segments across all available platforms")
    
    all_platforms_request = GetAudiencesRequest(
        audience_spec="Contextual segments for luxury automotive content",
        deliver_to=DeliverySpecification(
            platforms="all",
            countries=["US"]
        ),
        filters=AudienceFilters(
            data_providers=["Peer39"],
            catalog_types=["marketplace"]
        )
    )
    
    response = mcp.call_tool("get_audiences", **all_platforms_request.model_dump())
    print_response("All Platforms Discovery Response", response)
    
    # --- Step 3: Audience Activation ---
    print_step(3, "Audience Activation",
               "Activate an audience that requires deployment")
    
    activate_request = ActivateAudienceRequest(
        audience_agent_segment_id="peer39_luxury_auto",
        platform="pubmatic",
        account="brand-456-pm"
    )
    
    response = mcp.call_tool("activate_audience", **activate_request.model_dump())
    print_response("Activation Response", response)
    
    # --- Step 4: Status Check Before Activation ---
    print_step(4, "Status Check - Activating",
               "Check status immediately after activation request")
    
    status_request = CheckAudienceStatusRequest(
        audience_agent_segment_id="peer39_luxury_auto",
        decisioning_platform="pubmatic",
        account="brand-456-pm"
    )
    
    response = mcp.call_tool("check_audience_status", **status_request.model_dump())
    print_response("Status Check Response (Before)", response)
    
    # --- Step 5: Status Check After Activation ---
    print_step(5, "Status Check - Deployed",
               "Check status after activation completes (simulated)")
    
    console.print("[dim]Waiting for activation to complete...[/dim]")
    time.sleep(1)  # Simulate waiting
    
    response = mcp.call_tool("check_audience_status", **status_request.model_dump())
    print_response("Status Check Response (After)", response)
    
    # --- Summary ---
    console.print("\n[bold green]✅ Simulation Complete![/bold green]")
    console.print("\nThis simulation demonstrated:")
    
    features = Table(title="Protocol Features Demonstrated")
    features.add_column("Feature", style="cyan")
    features.add_column("Description", style="white")
    
    features.add_row("Multi-Platform Discovery", "Efficient discovery across multiple SSPs")
    features.add_row("All Platforms Discovery", "Data provider workflow showing all deployments")
    features.add_row("Audience Activation", "On-demand audience deployment")
    features.add_row("Status Monitoring", "Real-time activation status tracking")
    features.add_row("Lifecycle Management", "Activation and deployment workflow")
    
    console.print(features)
    
    console.print(f"\n[dim]For detailed protocol specification, see:")
    console.print(f"../adcontextprotocol/docs/audience/specification.md[/dim]")


if __name__ == "__main__":
    try:
        run_simulation()
    except Exception as e:
        console.print(f"[bold red]Simulation failed: {e}[/bold red]")
        raise