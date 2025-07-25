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
    
    # Build request
    request_data = {
        "audience_spec": audience_spec,
        "deliver_to": {
            "platforms": platforms,
            "countries": ["US"]
        },
        "max_results": 10
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
        response = result.data.model_dump() if hasattr(result, 'data') else result
        
        if not response.get("audiences"):
            console.print("[yellow]No audiences found matching your criteria[/yellow]")
            return
        
        # Display results
        console.print(f"\n[bold green]Found {len(response['audiences'])} audiences:[/bold green]")
        
        for i, audience in enumerate(response["audiences"], 1):
            console.print(f"\n[bold]{i}. {audience['name']}[/bold]")
            console.print(f"   Provider: {audience['data_provider']}")
            console.print(f"   Coverage: {audience['coverage_percentage']:.1f}%")
            console.print(f"   Type: {audience['audience_type']}")
            
            # Show pricing
            pricing = audience["pricing"]
            if pricing.get("cpm"):
                console.print(f"   CPM: ${pricing['cpm']:.2f}")
            if pricing.get("revenue_share_percentage"):
                console.print(f"   Revenue Share: {pricing['revenue_share_percentage']:.1f}%")
            
            # Show deployments
            console.print(f"   Deployments:")
            for dep in audience["deployments"]:
                status = "🟢 Live" if dep["is_live"] else "🟡 Needs Activation"
                account_info = f" (Account: {dep['account']})" if dep.get("account") else ""
                console.print(f"     • {dep['platform']}: {status}{account_info}")
            
            # Show match reason if available
            if audience.get("match_reason"):
                console.print(f"   [dim]Why: {audience['match_reason']}[/dim]")
        
        # Show custom segment proposals if available
        if response.get("custom_segment_proposals"):
            console.print(f"\n[bold yellow]💡 Custom Segment Proposals[/bold yellow]")
            console.print("[dim]These segments could be created for better targeting:[/dim]")
            
            for i, proposal in enumerate(response["custom_segment_proposals"], 1):
                console.print(f"\n[bold]{i}. {proposal['proposed_name']}[/bold]")
                console.print(f"   Target: {proposal['target_audience']}")
                console.print(f"   Coverage: {proposal['estimated_coverage_percentage']:.1f}%")
                console.print(f"   Est. CPM: ${proposal['estimated_cpm']:.2f}")
                console.print(f"   [dim]{proposal['creation_rationale']}[/dim]")
        
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
        audience_spec = " ".join(sys.argv[2:])
    else:
        audience_spec = Prompt.ask("Describe the audience you're looking for")
    
    request_data = {
        "audience_spec": audience_spec,
        "deliver_to": {
            "platforms": "all",
            "countries": ["US"]
        },
        "max_results": 5
    }
    
    client = Client("main.py")
    async with client:
        try:
            response = await client.call_tool("get_audiences", request_data)
            console.print(Panel(
                json.dumps(response, indent=2, default=str),
                title=f"Results for: {audience_spec}",
                border_style="green"
            ))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        asyncio.run(quick_prompt())
    else:
        asyncio.run(main())