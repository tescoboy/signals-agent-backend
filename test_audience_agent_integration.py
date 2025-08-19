#!/usr/bin/env python3
"""Test script for audience-agent integration."""

import asyncio
import requests
import json
from rich.console import Console
from rich.table import Table

console = Console()

def test_audience_agent_integration():
    """Test the audience-agent integration endpoints."""
    
    base_url = "http://localhost:8000"
    
    console.print("[bold cyan]Testing Audience Agent Integration[/bold cyan]")
    console.print("=" * 60)
    
    # Test 1: Get signals
    console.print("\n[bold yellow]1. Testing /audience-agent/signals[/bold yellow]")
    
    signals_request = {
        "signal_spec": "luxury automotive targeting",
        "deliver_to": {
            "platforms": "all",
            "countries": ["US"]
        },
        "max_results": 3
    }
    
    try:
        response = requests.post(
            f"{base_url}/audience-agent/signals",
            json=signals_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"✅ Success! Status: {response.status_code}")
            console.print(f"Source: {data.get('source')}")
            console.print(f"Query: {data.get('query')}")
            console.print(f"Total Signals: {data.get('total_signals')}")
            console.print(f"Total Custom Segments: {data.get('total_custom_segments')}")
            
            # Display signals in a table
            if data.get('signals'):
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("Signal", style="bold", min_width=30)
                table.add_column("Provider", style="blue", width=15)
                table.add_column("Coverage", justify="right", width=10)
                table.add_column("CPM", justify="right", width=8)
                
                for signal in data['signals']:
                    name = signal['name'][:40] + "..." if len(signal['name']) > 40 else signal['name']
                    coverage = f"{signal['coverage_percentage']:.1f}%"
                    cpm = f"${signal['pricing']['cpm']:.2f}" if signal['pricing']['cpm'] > 0 else "Free"
                    
                    table.add_row(
                        name,
                        signal['data_provider'],
                        coverage,
                        cpm
                    )
                
                console.print(table)
            
            # Display custom segments
            if data.get('custom_segments'):
                console.print(f"\n[bold yellow]Custom Segments:[/bold yellow]")
                for i, segment in enumerate(data['custom_segments'], 1):
                    console.print(f"[cyan]{i}.[/cyan] [bold]{segment['proposed_name']}[/bold]")
                    console.print(f"   Coverage: {segment['estimated_coverage_percentage']:.1f}% | CPM: ${segment['estimated_cpm']:.2f}")
                    console.print(f"   [dim]{segment['creation_rationale'][:100]}...[/dim]")
            
            # Store signal ID for activation test
            signal_id = None
            if data.get('signals'):
                signal_id = data['signals'][0]['signals_agent_segment_id']
            
            return signal_id, data.get('context_id')
            
        else:
            console.print(f"❌ Failed! Status: {response.status_code}")
            console.print(f"Response: {response.text}")
            return None, None
            
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return None, None
    
    # Test 2: Activate signal (if we got a signal ID)
    if signal_id:
        console.print(f"\n[bold yellow]2. Testing /audience-agent/activate[/bold yellow]")
        console.print(f"Activating signal: {signal_id[:50]}...")
        
        activation_request = {
            "signal_id": signal_id,
            "platform": "liveramp",
            "account": "test_account",
            "context_id": context_id
        }
        
        try:
            response = requests.post(
                f"{base_url}/audience-agent/activate",
                json=activation_request,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"✅ Success! Status: {response.status_code}")
                console.print(f"Activation Status: {data.get('status')}")
                console.print(f"Platform Segment ID: {data.get('platform_segment_id')}")
                console.print(f"Message: {data.get('message')}")
                
            else:
                console.print(f"❌ Failed! Status: {response.status_code}")
                console.print(f"Response: {response.text}")
                
        except Exception as e:
            console.print(f"❌ Error: {e}")

def test_health_endpoint():
    """Test the health endpoint."""
    
    base_url = "http://localhost:8000"
    
    console.print(f"\n[bold yellow]3. Testing Health Endpoint[/bold yellow]")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"✅ Health Check: {data.get('status')}")
            console.print(f"Version: {data.get('version')}")
            console.print(f"Protocols: {data.get('protocols')}")
        else:
            console.print(f"❌ Health Check Failed: {response.status_code}")
            
    except Exception as e:
        console.print(f"❌ Health Check Error: {e}")

if __name__ == "__main__":
    console.print("[bold magenta]Audience Agent Integration Test[/bold magenta]")
    console.print("Make sure your backend server is running on localhost:8000")
    console.print("=" * 60)
    
    # Test health first
    test_health_endpoint()
    
    # Test audience agent integration
    test_audience_agent_integration()
    
    console.print("\n[bold green]✅ Test Complete![/bold green]")
