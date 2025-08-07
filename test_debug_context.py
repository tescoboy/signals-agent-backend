#!/usr/bin/env python3
"""Debug contextual query handling."""

import requests
import json
from datetime import datetime
from rich.console import Console
from rich import print_json

console = Console()

def debug_context():
    base_url = "http://localhost:8000"
    
    # Step 1: Initial discovery query
    console.print("\n[bold]Initial Query:[/bold]")
    
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
    result = response.json()
    
    console.print("\n[bold]Response structure:[/bold]")
    print_json(data=result)
    
    # Check for context_id
    context_id = None
    if "result" in result and "parts" in result["result"]:
        for part in result["result"]["parts"]:
            console.print(f"\nPart type: {part.get('kind')}")
            if part.get("kind") == "data":
                data = part.get("data", {})
                console.print(f"Data keys: {list(data.keys())}")
                # Check nested content
                if "content" in data and isinstance(data["content"], dict):
                    console.print(f"Content keys: {list(data['content'].keys())}")
                    context_id = data["content"].get("context_id")
                else:
                    context_id = data.get("context_id")
                console.print(f"Found context_id: {context_id}")
    
    # Step 2: Try contextual query with context_id
    if context_id:
        console.print(f"\n[bold green]Testing with context_id: {context_id}[/bold green]")
        
        followup_request = {
            "type": "discovery",
            "contextId": context_id,
            "parameters": {
                "query": "tell me about the custom segments"
            }
        }
        
        response = requests.post(f"{base_url}/a2a/task", json=followup_request)
        result = response.json()
        
        console.print("\n[bold]Follow-up response:[/bold]")
        
        if "status" in result and "message" in result["status"]:
            message = result["status"]["message"]
            if "parts" in message:
                for part in message["parts"]:
                    if part.get("kind") == "text":
                        console.print(f"Text: {part['text'][:200]}...")
                        break

if __name__ == "__main__":
    debug_context()