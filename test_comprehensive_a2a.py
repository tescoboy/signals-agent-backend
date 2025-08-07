#!/usr/bin/env python3
"""Comprehensive A2A testing to demonstrate all fixes working."""

import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_agent_card():
    """Test agent card retrieval."""
    console.print("\n[bold blue]Testing Agent Card[/bold blue]")
    
    try:
        response = requests.get("http://localhost:8000/agent-card")
        
        if response.status_code == 200:
            card = response.json()
            console.print(f"[green]✓ Agent Card: {card['name']} v{card['version']}[/green]")
            console.print(f"  Skills: {len(card.get('skills', []))}")
            return True
        else:
            console.print(f"[red]✗ Agent Card failed: {response.status_code}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Agent Card error: {e}[/red]")
        return False


def test_json_rpc_message():
    """Test JSON-RPC message/send format that A2A Inspector uses."""
    console.print("\n[bold blue]Testing JSON-RPC message/send (A2A Inspector Format)[/bold blue]")
    
    request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": "inspector-test-123",
        "params": {
            "message": {
                "parts": [{
                    "kind": "text",
                    "text": "sports car enthusiasts"
                }],
                "role": "user"
            }
        }
    }
    
    try:
        response = requests.post("http://localhost:8000/", json=request)
        
        if response.status_code == 200:
            result = response.json()
            
            # Validate JSON-RPC structure
            if "jsonrpc" in result and "id" in result and "result" in result:
                console.print("[green]✓ JSON-RPC wrapper correct[/green]")
                
                # Validate Message structure 
                message = result["result"]
                if message.get("kind") == "message" and "message_id" in message:
                    console.print("[green]✓ Message structure correct[/green]")
                    
                    # Check role
                    if message.get("role") == "agent":
                        console.print("[green]✓ Role is 'agent' (A2A compliant)[/green]")
                    else:
                        console.print(f"[red]✗ Wrong role: {message.get('role')}[/red]")
                    
                    # Check parts
                    parts = message.get("parts", [])
                    if parts:
                        text_parts = [p for p in parts if p.get("kind") == "text"]
                        data_parts = [p for p in parts if p.get("kind") == "data"]
                        
                        console.print(f"[green]✓ Parts: {len(text_parts)} text, {len(data_parts)} data[/green]")
                        
                        # Check TextPart format
                        if text_parts and "text" in text_parts[0]:
                            console.print("[green]✓ TextPart has 'text' field[/green]")
                        
                        # Check DataPart format
                        if data_parts and "data" in data_parts[0]:
                            console.print("[green]✓ DataPart has 'data' field[/green]")
                    
                    return True
                else:
                    console.print("[red]✗ Invalid Message structure[/red]")
                    return False
            else:
                console.print("[red]✗ Invalid JSON-RPC structure[/red]")
                return False
        else:
            console.print(f"[red]✗ HTTP error: {response.status_code}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False


def test_a2a_task_format():
    """Test standard A2A task format."""
    console.print("\n[bold blue]Testing Standard A2A Task Format[/bold blue]")
    
    task = {
        "taskId": "test-task-456",
        "type": "discovery",
        "parameters": {
            "query": "luxury travel",
            "max_results": 3
        }
    }
    
    try:
        response = requests.post("http://localhost:8000/a2a/task", json=task)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("kind") == "task" and result.get("status") == "Completed":
                console.print("[green]✓ Task format correct[/green]")
                console.print(f"  Task ID: {result.get('id')}")
                console.print(f"  Context ID: {result.get('contextId')}")
                
                # Check output structure
                output = result.get("output", {})
                parts = output.get("parts", [])
                if parts:
                    content = parts[0].get("content", {})
                    signals = content.get("signals", [])
                    console.print(f"[green]✓ Found {len(signals)} signals[/green]")
                
                return True
            else:
                console.print("[red]✗ Invalid task response format[/red]")
                return False
        else:
            console.print(f"[red]✗ HTTP error: {response.status_code}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False


def test_a2a_validation():
    """Test validation against official A2A SDK."""
    console.print("\n[bold blue]Testing A2A SDK Validation[/bold blue]")
    
    try:
        from a2a.types import Message, TextPart, DataPart, Role
        
        # Get a real response
        request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": "validation-456",
            "params": {
                "message": {
                    "parts": [{"kind": "text", "text": "health and fitness"}],
                    "role": "user"
                }
            }
        }
        
        response = requests.post("http://localhost:8000/", json=request)
        result = response.json()
        message_data = result["result"]
        
        # Validate each part
        validated_parts = []
        for part in message_data["parts"]:
            if part["kind"] == "text":
                validated_parts.append(TextPart(kind="text", text=part["text"]))
            elif part["kind"] == "data":
                validated_parts.append(DataPart(kind="data", data=part["data"]))
        
        # Validate complete message
        message = Message(
            kind="message",
            message_id=message_data["message_id"],
            parts=validated_parts,
            role=Role(message_data["role"])
        )
        
        console.print("[green]✓ A2A SDK validation passed![/green]")
        console.print(f"  Role: {message.role.value}")
        console.print(f"  Parts: {len(message.parts)}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ A2A validation failed: {e}[/red]")
        return False


def main():
    """Run comprehensive A2A tests."""
    console.print(Panel(
        "[bold cyan]🎯 Comprehensive A2A Protocol Test Suite[/bold cyan]\n"
        "Testing all aspects of A2A compliance after validation fixes",
        border_style="blue"
    ))
    
    results = {}
    
    # Run all tests
    results["Agent Card"] = test_agent_card()
    results["JSON-RPC Message"] = test_json_rpc_message() 
    results["A2A Task"] = test_a2a_task_format()
    results["SDK Validation"] = test_a2a_validation()
    
    # Summary table
    console.print("\n[bold]Test Results Summary:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Test", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Description", style="dim")
    
    descriptions = {
        "Agent Card": "A2A agent discovery metadata",
        "JSON-RPC Message": "A2A Inspector message/send format",
        "A2A Task": "Standard A2A task format",
        "SDK Validation": "Official A2A SDK validation"
    }
    
    for test_name, passed in results.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        table.add_row(test_name, status, descriptions[test_name])
    
    console.print(table)
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        console.print("\n[bold green]🎉 All A2A validation fixes working correctly![/bold green]")
        console.print("The agent is now fully compatible with A2A Inspector and official A2A SDK.")
    else:
        console.print("\n[bold red]❌ Some tests failed[/bold red]")
        console.print("Please review the failed tests above.")
    
    return all_passed


if __name__ == "__main__":
    main()