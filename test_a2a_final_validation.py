#!/usr/bin/env python3
"""Final validation test for A2A Message format."""

import requests
import json
from rich.console import Console

console = Console()

def test_real_response_validation():
    """Test that our real response validates against A2A types."""
    
    # Send a test request to get a real response
    request = {
        "jsonrpc": "2.0",
        "method": "message/send", 
        "id": "validation-test",
        "params": {
            "message": {
                "parts": [{
                    "kind": "text",
                    "text": "sports fans"
                }],
                "role": "user"
            }
        }
    }
    
    console.print("[bold blue]Testing real response validation[/bold blue]")
    
    try:
        response = requests.post("http://localhost:8000/", json=request)
        
        if response.status_code == 200:
            result = response.json()
            message_response = result.get("result", {})
            
            # Now validate this response using A2A types
            try:
                from a2a.types import Message, TextPart, DataPart
                
                # Extract the response parts
                parts_data = message_response.get("parts", [])
                validated_parts = []
                
                for part in parts_data:
                    if part.get("kind") == "text":
                        # Create TextPart
                        text_part = TextPart(
                            kind="text",
                            text=part["text"]
                        )
                        validated_parts.append(text_part)
                        console.print(f"[green]✓ TextPart validated: {part['text'][:50]}...[/green]")
                        
                    elif part.get("kind") == "data":
                        # Create DataPart 
                        data_part = DataPart(
                            kind="data",
                            data=part["data"]
                        )
                        validated_parts.append(data_part)
                        console.print("[green]✓ DataPart validated[/green]")
                
                # Create and validate complete Message
                message = Message(
                    kind=message_response["kind"],
                    message_id=message_response["message_id"],  # Fixed: use message_id
                    parts=validated_parts,
                    role=message_response["role"]
                )
                
                console.print("[bold green]✓ Complete Message validation passed![/bold green]")
                console.print(f"Message ID: {message.message_id}")  # Fixed: use message_id
                console.print(f"Role: {message.role}")
                console.print(f"Parts count: {len(message.parts)}")
                
                return True
                
            except Exception as e:
                console.print(f"[red]✗ A2A validation failed: {e}[/red]")
                return False
                
        else:
            console.print(f"[red]HTTP Error: {response.status_code}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]Request failed: {e}[/red]")
        return False


if __name__ == "__main__":
    success = test_real_response_validation()
    if success:
        console.print("\n[bold green]🎉 A2A format validation successful![/bold green]")
        console.print("The agent now returns properly formatted A2A Messages.")
    else:
        console.print("\n[bold red]❌ A2A validation failed[/bold red]")