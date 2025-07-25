#!/usr/bin/env python3
"""Interactive client for testing the Audience Activation Protocol."""

import asyncio
import json
import sys
from typing import Dict, Any
from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from schemas import *

console = Console()

def print_banner():
    """Print the client banner."""
    console.print(Panel(
        "[bold cyan]🎯 Audience Activation Protocol Client[/bold cyan]\n"
        "Interactive client for testing audience discovery and activation",
        border_style="blue"
    ))

def print_help():
    """Print available commands."""
    console.print("\n[bold]Available Commands:[/bold]")
    
    commands = Table()
    commands.add_column("Command", style="cyan", width=20)
    commands.add_column("Description", style="white")
    
    commands.add_row("discover", "Discover audiences with natural language")
    commands.add_row("activate", "Activate an audience on a platform")
    commands.add_row("status", "Check audience activation status")
    commands.add_row("help", "Show this help message")
    commands.add_row("quit", "Exit the client")
    
    console.print(commands)

async def discover_audiences(client: Client):
    """Interactive audience discovery."""
    console.print("\n[bold blue]🔍 Audience Discovery[/bold blue]")
    
    # Get audience specification
    audience_spec = Prompt.ask("Describe the audience you're looking for")
    
    # Get platforms
    console.print("\nSelect platforms:")
    console.print("1. Specific platforms")
    console.print("2. All platforms")
    
    platform_choice = Prompt.ask("Choice", choices=["1", "2"], default="2")
    
    if platform_choice == "1":
        available_platforms = [
            "the-trade-desk", "index-exchange", "openx", 
            "pubmatic", "google-dv360", "amazon-dsp"
        ]
        console.print(f"\nAvailable platforms: {', '.join(available_platforms)}")
        platform_input = Prompt.ask("Enter platforms (comma-separated)")
        platforms = [{"platform": p.strip()} for p in platform_input.split(",")]
    else:
        platforms = "all"
    
    # Get filters
    max_cpm = Prompt.ask("Maximum CPM (optional)", default="")
    data_provider = Prompt.ask("Data provider filter (optional)", default="")
    max_results = Prompt.ask("Number of results", default="5")
    
    # Build request
    try:
        max_results_int = int(max_results)
    except ValueError:
        max_results_int = 5
        console.print("[yellow]Invalid number, using default of 5[/yellow]")
    
    request_data = {
        "audience_spec": audience_spec,
        "deliver_to": {
            "platforms": platforms,
            "countries": ["US"]
        },
        "max_results": max_results_int
    }
    
    filters = {}
    if max_cpm:
        try:
            filters["max_cpm"] = float(max_cpm)
        except ValueError:
            console.print("[red]Invalid CPM value, ignoring[/red]")
    
    if data_provider:
        filters["data_providers"] = [data_provider]
    
    if filters:
        request_data["filters"] = filters
    
    # Make request via MCP
    try:
        console.print("\n[dim]Searching for audiences...[/dim]")
        result = await client.call_tool("get_audiences", request_data)
        # Convert response to dict for easier handling
        if hasattr(result, 'model_dump'):
            response = result.model_dump()
        elif hasattr(result, 'dict'):
            response = result.dict()
        elif isinstance(result, dict):
            response = result
        else:
            # Fallback: try to access common attributes
            response = {
                "audiences": getattr(result, 'audiences', []),
                "custom_segment_proposals": getattr(result, 'custom_segment_proposals', [])
            }
        
        if not response.get("audiences"):
            console.print("[yellow]No audiences found matching your criteria[/yellow]")
            return
        
        # Display results in an attractive table format
        console.print(f"\n[bold green]🎯 Found {len(response['audiences'])} audiences[/bold green]")
        
        # Create main results table
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("#", style="dim", width=3)
        table.add_column("Audience", style="bold", min_width=20)
        table.add_column("Provider", style="blue", width=12)
        table.add_column("Coverage", justify="right", width=8)
        table.add_column("CPM", justify="right", width=8)
        table.add_column("Status", width=12)
        
        for i, audience in enumerate(response["audiences"], 1):
            # Determine status from deployments
            live_count = sum(1 for dep in audience["deployments"] if dep["is_live"])
            total_count = len(audience["deployments"])
            
            if live_count == total_count:
                status = "🟢 All Live"
            elif live_count > 0:
                status = f"🟡 {live_count}/{total_count} Live"
            else:
                status = "⚪ Needs Setup"
            
            # Format pricing
            pricing = audience["pricing"]
            if pricing.get("cpm"):
                cpm_str = f"${pricing['cpm']:.2f}"
            elif pricing.get("revenue_share_percentage"):
                cpm_str = f"{pricing['revenue_share_percentage']:.1f}%"
            else:
                cpm_str = "N/A"
            
            table.add_row(
                str(i),
                audience['name'][:40] + "..." if len(audience['name']) > 40 else audience['name'],
                audience['data_provider'],
                f"{audience['coverage_percentage']:.1f}%",
                cpm_str,
                status
            )
        
        console.print(table)
        
        # Show detailed match reasons
        if any(aud.get("match_reason") for aud in response["audiences"]):
            console.print("\n[bold yellow]🧠 AI Match Explanations[/bold yellow]")
            for i, audience in enumerate(response["audiences"], 1):
                if audience.get("match_reason"):
                    console.print(f"[dim]{i}.[/dim] [bold]{audience['name']}[/bold]")
                    console.print(f"   [italic]{audience['match_reason']}[/italic]\n")
        
        # Show custom segment proposals if available
        if response.get("custom_segment_proposals"):
            console.print(f"\n[bold yellow]💡 Custom Segment Proposals[/bold yellow]")
            console.print("[dim]AI-suggested segments that could be created for better targeting:[/dim]\n")
            
            # Create proposals table
            proposals_table = Table(show_header=True, header_style="bold yellow", box=None)
            proposals_table.add_column("Proposed Segment", style="bold", min_width=25)
            proposals_table.add_column("Coverage", justify="right", width=10)
            proposals_table.add_column("Est. CPM", justify="right", width=10)
            proposals_table.add_column("Rationale", style="dim", min_width=30)
            
            for proposal in response["custom_segment_proposals"]:
                proposals_table.add_row(
                    proposal['proposed_name'],
                    f"{proposal['estimated_coverage_percentage']:.1f}%",
                    f"${proposal['estimated_cpm']:.2f}",
                    proposal['creation_rationale'][:60] + "..." if len(proposal['creation_rationale']) > 60 else proposal['creation_rationale']
                )
            
            console.print(proposals_table)
            
            # Show IDs for activation
            console.print("\n[dim]To activate a custom segment, use the activate command with these IDs:[/dim]")
            for proposal in response["custom_segment_proposals"]:
                console.print(f"  [cyan]{proposal['custom_segment_id']}[/cyan] - {proposal['proposed_name']}")
        
        return response["audiences"]
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

async def activate_audience(client: Client):
    """Interactive audience activation."""
    console.print("\n[bold blue]🚀 Audience Activation[/bold blue]")
    
    segment_id = Prompt.ask("Audience segment ID")
    platform = Prompt.ask("Platform")
    account = Prompt.ask("Account (optional)", default="")
    
    request_data = {
        "audience_agent_segment_id": segment_id,
        "platform": platform
    }
    
    if account:
        request_data["account"] = account
    
    try:
        console.print("\n[dim]Activating audience...[/dim]")
        response = await client.call_tool("activate_audience", request_data)
        
        console.print(f"[bold green]✅ Activation initiated![/bold green]")
        console.print(f"Platform Segment ID: {response['decisioning_platform_segment_id']}")
        console.print(f"Estimated Duration: {response['estimated_activation_duration_minutes']} minutes")
        
        return response
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

async def check_status(client: Client):
    """Interactive status checking."""
    console.print("\n[bold blue]📊 Status Check[/bold blue]")
    
    segment_id = Prompt.ask("Audience segment ID")
    platform = Prompt.ask("Platform")
    account = Prompt.ask("Account (optional)", default="")
    
    request_data = {
        "audience_agent_segment_id": segment_id,
        "decisioning_platform": platform
    }
    
    if account:
        request_data["account"] = account
    
    try:
        response = await client.call_tool("check_audience_status", request_data)
        
        status_emoji = {
            "deployed": "🟢",
            "activating": "🟡", 
            "failed": "🔴",
            "not_found": "❓"
        }
        
        emoji = status_emoji.get(response["status"], "❓")
        console.print(f"\n{emoji} Status: [bold]{response['status'].upper()}[/bold]")
        
        if response.get("deployed_at"):
            console.print(f"Deployed: {response['deployed_at']}")
        
        if response.get("error_message"):
            console.print(f"[red]Error: {response['error_message']}[/red]")
        
        return response
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

async def main():
    """Main client loop."""
    print_banner()
    print_help()
    
    client = Client("main.py")
    
    async with client:
        while True:
            try:
                command = Prompt.ask("\n[bold]Enter command[/bold]", default="discover").lower()
                
                if command in ["quit", "exit", "q"]:
                    console.print("\n[dim]Goodbye! 👋[/dim]")
                    break
                elif command in ["help", "h"]:
                    print_help()
                elif command in ["discover", "d"]:
                    await discover_audiences(client)
                elif command in ["activate", "a"]:
                    await activate_audience(client)
                elif command in ["status", "s"]:
                    await check_status(client)
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    print_help()
            
            except KeyboardInterrupt:
                console.print("\n\n[dim]Goodbye! 👋[/dim]")
                break
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")

async def quick_prompt():
    """Quick prompt mode for one-off queries."""
    if len(sys.argv) > 2:
        if sys.argv[2] == "--limit" and len(sys.argv) > 4:
            max_results = int(sys.argv[3])
            audience_spec = " ".join(sys.argv[4:])
        else:
            max_results = 5
            audience_spec = " ".join(sys.argv[2:])
    else:
        audience_spec = Prompt.ask("Describe the audience you're looking for")
        max_results = 5
    
    request_data = {
        "audience_spec": audience_spec,
        "deliver_to": {
            "platforms": "all",
            "countries": ["US"]
        },
        "max_results": max_results
    }
    
    client = Client("main.py")
    async with client:
        try:
            console.print(f"\n[bold cyan]🔍 Searching for: {audience_spec}[/bold cyan]")
            console.print(f"[dim]Limiting to top {max_results} results[/dim]\n")
            
            result = await client.call_tool("get_audiences", request_data)
            # Convert response to dict for easier handling
            if hasattr(result, 'model_dump'):
                response = result.model_dump()
            elif hasattr(result, 'dict'):
                response = result.dict()
            elif isinstance(result, dict):
                response = result
            else:
                # Fallback: try to access common attributes
                response = {
                    "audiences": getattr(result, 'audiences', []),
                    "custom_segment_proposals": getattr(result, 'custom_segment_proposals', [])
                }
            
            if not response.get("audiences"):
                console.print("[yellow]No audiences found matching your criteria[/yellow]")
                return
            
            # Display results using the same attractive format as interactive mode
            console.print(f"[bold green]🎯 Found {len(response['audiences'])} audiences[/bold green]")
            
            # Create main results table
            table = Table(show_header=True, header_style="bold cyan", box=None)
            table.add_column("#", style="dim", width=3)
            table.add_column("Audience", style="bold", min_width=25)
            table.add_column("Provider", style="blue", width=12)
            table.add_column("Coverage", justify="right", width=8)
            table.add_column("CPM", justify="right", width=8)
            table.add_column("Status", width=12)
            
            for i, audience in enumerate(response["audiences"], 1):
                # Determine status from deployments
                live_count = sum(1 for dep in audience["deployments"] if dep["is_live"])
                total_count = len(audience["deployments"])
                
                if live_count == total_count:
                    status = "🟢 All Live"
                elif live_count > 0:
                    status = f"🟡 {live_count}/{total_count} Live"
                else:
                    status = "⚪ Needs Setup"
                
                # Format pricing
                pricing = audience["pricing"]
                if pricing.get("cpm"):
                    cpm_str = f"${pricing['cpm']:.2f}"
                elif pricing.get("revenue_share_percentage"):
                    cpm_str = f"{pricing['revenue_share_percentage']:.1f}%"
                else:
                    cpm_str = "N/A"
                
                table.add_row(
                    str(i),
                    audience['name'][:35] + "..." if len(audience['name']) > 35 else audience['name'],
                    audience['data_provider'],
                    f"{audience['coverage_percentage']:.1f}%",
                    cpm_str,
                    status
                )
            
            console.print(table)
            
            # Show AI match explanations
            if any(aud.get("match_reason") for aud in response["audiences"]):
                console.print("\n[bold yellow]🧠 AI Match Explanations[/bold yellow]")
                for i, audience in enumerate(response["audiences"], 1):
                    if audience.get("match_reason"):
                        console.print(f"[dim]{i}.[/dim] [bold]{audience['name']}[/bold]")
                        console.print(f"   [italic]{audience['match_reason']}[/italic]\n")
            
            # Show custom segment proposals
            if response.get("custom_segment_proposals"):
                console.print(f"\n[bold yellow]💡 Custom Segment Proposals[/bold yellow]")
                console.print("[dim]AI-suggested segments that could be created:[/dim]\n")
                
                for i, proposal in enumerate(response["custom_segment_proposals"], 1):
                    console.print(f"[bold]{i}. {proposal['proposed_name']}[/bold]")
                    console.print(f"   ID: [cyan]{proposal['custom_segment_id']}[/cyan] (use this ID to activate)")
                    console.print(f"   Coverage: {proposal['estimated_coverage_percentage']:.1f}% | CPM: ${proposal['estimated_cpm']:.2f}")
                    console.print(f"   [italic]{proposal['creation_rationale']}[/italic]\n")
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        asyncio.run(quick_prompt())
    else:
        asyncio.run(main())