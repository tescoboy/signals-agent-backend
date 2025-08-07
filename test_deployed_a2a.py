#!/usr/bin/env python3
"""Test the deployed A2A server at audience-agent.fly.dev"""

import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BASE_URL = "https://audience-agent.fly.dev"

def test_agent_card():
    """Test the agent card endpoint."""
    console.print("\n[bold cyan]Testing Agent Card[/bold cyan]")
    response = requests.get(f"{BASE_URL}/agent-card")
    console.print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        console.print(f"✓ Agent: {data.get('name')}")
        console.print(f"  Version: {data.get('version')}")
        console.print(f"  Provider: {data.get('provider', {}).get('organization')}")
        return True
    else:
        console.print(f"✗ Error: {response.text}")
        return False

def test_json_rpc_message():
    """Test JSON-RPC message/send format."""
    console.print("\n[bold cyan]Testing JSON-RPC message/send[/bold cyan]")
    
    payload = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "message/send",
        "params": {
            "message": {
                "parts": [
                    {"kind": "text", "text": "test query for luxury cars"}
                ],
                "role": "user"
            }
        }
    }
    
    console.print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        console.print(f"Status: {response.status_code}")
        console.print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for JSON-RPC error
            if "error" in data:
                console.print(f"✗ JSON-RPC Error: {data['error']}")
                return False
            
            # Validate response structure
            if "result" in data:
                result = data["result"]
                if result.get("kind") == "message" and result.get("role") == "agent":
                    console.print("✓ Valid A2A message response")
                    return True
                else:
                    console.print(f"✗ Invalid result structure: {result}")
                    return False
        else:
            console.print(f"✗ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        console.print(f"✗ Exception: {e}")
        return False

def test_standard_task():
    """Test standard A2A task format."""
    console.print("\n[bold cyan]Testing Standard A2A Task[/bold cyan]")
    
    payload = {
        "taskId": "test-task-123",
        "type": "discovery",
        "parameters": {
            "query": "automotive enthusiasts",
            "max_results": 5
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/a2a/task",
            json=payload,
            timeout=30
        )
        
        console.print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("kind") == "task":
                console.print("✓ Valid task response")
                console.print(f"  Task ID: {data.get('id')}")
                console.print(f"  State: {data.get('status', {}).get('state')}")
                return True
            else:
                console.print(f"✗ Invalid response: {data}")
                return False
        else:
            console.print(f"✗ Error: {response.text}")
            return False
            
    except Exception as e:
        console.print(f"✗ Exception: {e}")
        return False

def main():
    console.print(Panel.fit(
        "🚀 Testing Deployed A2A Server\n"
        f"URL: {BASE_URL}",
        title="A2A Deployment Test"
    ))
    
    results = []
    
    # Run tests
    results.append(("Agent Card", test_agent_card()))
    results.append(("JSON-RPC Message", test_json_rpc_message()))
    results.append(("Standard Task", test_standard_task()))
    
    # Summary
    console.print("\n[bold cyan]Test Results[/bold cyan]")
    table = Table()
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="green")
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        style = "green" if passed else "red"
        table.add_row(test_name, f"[{style}]{status}[/{style}]")
    
    console.print(table)
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        console.print("\n✅ [green]All tests passed![/green]")
    else:
        console.print("\n❌ [red]Some tests failed[/red]")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())