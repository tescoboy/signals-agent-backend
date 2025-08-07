#!/usr/bin/env python3
"""Test A2A format validation issues."""

import requests
import json
from rich.console import Console

console = Console()

def test_json_rpc_message():
    """Test JSON-RPC message format that A2A Inspector uses."""
    
    # This is the format that A2A Inspector sends
    request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": "test-001",
        "params": {
            "message": {
                "parts": [{
                    "kind": "text", 
                    "text": "luxury car buyers"
                }],
                "role": "user"
            }
        }
    }
    
    console.print("[bold blue]Testing JSON-RPC message/send format[/bold blue]")
    console.print(f"Request: {json.dumps(request, indent=2)}")
    
    try:
        response = requests.post("http://localhost:8000/", json=request)
        console.print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            console.print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if the response follows A2A Message format
            message_response = result.get("result", {})
            if message_response.get("kind") == "message":
                console.print("[green]✓ Response has correct Message format[/green]")
                
                # Check parts structure
                parts = message_response.get("parts", [])
                if parts:
                    console.print(f"Parts count: {len(parts)}")
                    for i, part in enumerate(parts):
                        console.print(f"Part {i}: {part.get('contentType', 'unknown type')}")
                        
                        # Check if it's a TextPart
                        if part.get("contentType") == "text/plain":
                            console.print(f"  Text: {part.get('content', '')[:100]}...")
                        elif part.get("contentType") == "application/json":
                            content = part.get("content", {})
                            if isinstance(content, dict):
                                signals_count = len(content.get("signals", []))
                                console.print(f"  JSON content with {signals_count} signals")
                
                # Check role
                role = message_response.get("role")
                console.print(f"Role: {role}")
                if role == "assistant":
                    console.print("[yellow]⚠ Role is 'assistant' but A2A might expect 'agent'[/yellow]")
                
            else:
                console.print("[red]✗ Response missing 'kind' field or not 'message'[/red]")
        else:
            console.print(f"[red]Error: {response.text}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def test_a2a_message_validation():
    """Test message format validation using a2a types."""
    try:
        from a2a.types import Message, TextPart, Role
        
        console.print("\n[bold blue]Testing A2A Message validation[/bold blue]")
        
        # Test 1: Current format (should fail)
        try:
            current_format = Message(
                kind="message",
                messageId="msg_123",
                parts=[{
                    "contentType": "application/json", 
                    "content": {"test": "data"}
                }],
                role="assistant"  # This might be wrong
            )
            console.print("[green]✓ Current format passed validation[/green]")
        except Exception as e:
            console.print(f"[red]✗ Current format failed: {e}[/red]")
        
        # Test 2: Try with TextPart
        try:
            text_part_format = Message(
                kind="message",
                messageId="msg_124", 
                parts=[
                    TextPart(
                        kind="text",
                        text="Found 3 luxury car buyer segments"
                    )
                ],
                role="agent"  # Try with 'agent' instead of 'assistant'
            )
            console.print("[green]✓ TextPart format passed validation[/green]")
        except Exception as e:
            console.print(f"[red]✗ TextPart format failed: {e}[/red]")
            
        # Test 3: Check valid Role values
        try:
            from a2a.types import Role
            valid_roles = [role.value for role in Role]
            console.print(f"Valid roles: {valid_roles}")
        except:
            console.print("Could not get valid Role enum values")
            
    except ImportError:
        console.print("[yellow]A2A types not available for validation[/yellow]")


if __name__ == "__main__":
    test_json_rpc_message()
    test_a2a_message_validation()