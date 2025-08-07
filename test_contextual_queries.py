#!/usr/bin/env python3
"""Test contextual query handling in A2A protocol."""

import requests
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_contextual_queries():
    """Test that follow-up queries are handled contextually."""
    
    base_url = "http://localhost:8000"
    
    console.print(Panel.fit(
        "[bold blue]🔍 Testing Contextual Query Handling[/bold blue]\n"
        "Verifying follow-up queries work correctly",
        title="Contextual Query Test"
    ))
    
    # Step 1: Initial discovery query
    console.print("\n[bold]1. Initial Discovery Query:[/bold] 'sports audiences'")
    
    initial_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "message_id": f"msg_{datetime.now().timestamp()}",
                "parts": [{
                    "kind": "text",
                    "text": "sports audiences"
                }],
                "role": "user"
            }
        },
        "id": "test-initial"
    }
    
    response = requests.post(base_url, json=initial_request)
    initial_result = response.json()
    
    # Extract context_id from the response
    context_id = None
    if "result" in initial_result and "parts" in initial_result["result"]:
        for part in initial_result["result"]["parts"]:
            if part.get("kind") == "data" and "data" in part:
                # Handle nested content structure
                data = part["data"]
                if "content" in data and isinstance(data["content"], dict):
                    context_id = data["content"].get("context_id")
                else:
                    context_id = data.get("context_id")
                break
    
    # Display initial result
    if "result" in initial_result and "parts" in initial_result["result"]:
        for part in initial_result["result"]["parts"]:
            if part.get("kind") == "text":
                console.print(f"  Response: [green]{part['text'][:200]}...[/green]")
                break
    
    console.print(f"  Context ID: [cyan]{context_id}[/cyan]")
    
    # Step 2: Follow-up contextual query
    console.print("\n[bold]2. Follow-up Query:[/bold] 'tell me about the custom segments'")
    
    followup_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "message_id": f"msg_{datetime.now().timestamp()}",
                "parts": [{
                    "kind": "text",
                    "text": "tell me about the custom segments"
                }],
                "role": "user"
            },
            "contextId": context_id  # Include context from previous query
        },
        "id": "test-followup"
    }
    
    response = requests.post(base_url, json=followup_request)
    followup_result = response.json()
    
    # Check if the response is contextual or another discovery query
    is_contextual = False
    response_text = ""
    
    if "result" in followup_result and "parts" in followup_result["result"]:
        for part in followup_result["result"]["parts"]:
            if part.get("kind") == "text":
                response_text = part["text"]
                # Check if it's explaining custom segments vs searching for them
                if any(phrase in response_text.lower() for phrase in [
                    "custom segments are",
                    "ai-generated",
                    "proposals",
                    "can be created"
                ]):
                    is_contextual = True
                break
    
    console.print(f"  Response: [{'green' if is_contextual else 'red'}]{response_text[:200]}...[/{'green' if is_contextual else 'red'}]")
    console.print(f"  Contextual Response: [{'green' if is_contextual else 'red'}]{'✓ YES' if is_contextual else '✗ NO'}[/{'green' if is_contextual else 'red'}]")
    
    # Step 3: Test with explicit context in task format
    console.print("\n[bold]3. Task Format with Context:[/bold] 'tell me about the custom segments'")
    
    task_request = {
        "type": "discovery",
        "contextId": context_id,
        "parameters": {
            "query": "tell me about the custom segments"
        }
    }
    
    response = requests.post(f"{base_url}/a2a/task", json=task_request)
    task_result = response.json()
    
    # Check the task response
    task_is_contextual = False
    task_response_text = ""
    
    if "status" in task_result and "message" in task_result["status"]:
        message = task_result["status"]["message"]
        if "parts" in message:
            for part in message["parts"]:
                if part.get("kind") == "text":
                    task_response_text = part["text"]
                    if any(phrase in task_response_text.lower() for phrase in [
                        "custom segments are",
                        "ai-generated",
                        "proposals",
                        "can be created"
                    ]):
                        task_is_contextual = True
                    break
    
    console.print(f"  Response: [{'green' if task_is_contextual else 'red'}]{task_response_text[:200]}...[/{'green' if task_is_contextual else 'red'}]")
    console.print(f"  Contextual Response: [{'green' if task_is_contextual else 'red'}]{'✓ YES' if task_is_contextual else '✗ NO'}[/{'green' if task_is_contextual else 'red'}]")
    
    # Summary
    console.print("\n" + "="*60)
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="bold")
    table.add_column("Status")
    
    table.add_row(
        "Initial Query",
        "Returns segments",
        "[green]✓ PASS[/green]" if context_id else "[red]✗ FAIL[/red]"
    )
    
    table.add_row(
        "Follow-up (JSON-RPC)",
        "Contextual response",
        "[green]✓ PASS[/green]" if is_contextual else "[red]✗ FAIL[/red]"
    )
    
    table.add_row(
        "Follow-up (Task)",
        "Contextual response",
        "[green]✓ PASS[/green]" if task_is_contextual else "[red]✗ FAIL[/red]"
    )
    
    console.print(table)
    
    if is_contextual and task_is_contextual:
        console.print("\n[bold green]✅ Contextual query handling is working correctly![/bold green]")
    else:
        console.print("\n[bold red]❌ Contextual queries are being treated as new searches[/bold red]")
        console.print("[yellow]The agent should recognize follow-up questions and respond contextually.[/yellow]")

if __name__ == "__main__":
    test_contextual_queries()