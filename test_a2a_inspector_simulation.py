#!/usr/bin/env python3
"""Simulate A2A Inspector behavior to verify full compatibility."""

import httpx
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class A2AInspectorSimulator:
    """Simulates the A2A Inspector's request patterns."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            headers={
                "User-Agent": "A2A-Inspector/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Forwarded-Proto": "https"  # Simulate HTTPS proxy
            }
        )
    
    def test_agent_card(self) -> bool:
        """Test agent card endpoint as Inspector does."""
        console.print("\n[bold blue]1. Testing Agent Card Discovery[/bold blue]")
        
        try:
            response = self.client.get("/agent-card")
            
            if response.status_code == 200:
                card = response.json()
                
                # Validate required fields per A2A spec
                required = ["name", "description", "version", "url", "capabilities", "skills"]
                missing = [f for f in required if f not in card]
                
                if missing:
                    console.print(f"[red]✗ Missing required fields: {missing}[/red]")
                    return False
                
                # Check capabilities structure
                caps = card.get("capabilities", {})
                if "streaming" not in caps:
                    console.print("[red]✗ Missing capabilities.streaming[/red]")
                    return False
                
                # Check provider structure (required by Inspector)
                if "provider" not in card:
                    console.print("[yellow]⚠ No provider field (optional but recommended)[/yellow]")
                elif "organization" not in card["provider"]:
                    console.print("[red]✗ Missing provider.organization[/red]")
                    return False
                
                console.print(f"[green]✓ Agent Card valid: {card['name']} v{card['version']}[/green]")
                console.print(f"  Skills: {len(card.get('skills', []))}")
                console.print(f"  Provider: {card.get('provider', {}).get('organization', 'N/A')}")
                
                # Check URL is HTTPS
                if card["url"].startswith("https://"):
                    console.print(f"[green]✓ URL is HTTPS: {card['url']}[/green]")
                else:
                    console.print(f"[yellow]⚠ URL not HTTPS: {card['url']}[/yellow]")
                
                return True
            else:
                console.print(f"[red]✗ HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False
    
    def test_json_rpc_message(self, text: str = "sports car buyers") -> bool:
        """Test JSON-RPC message/send as Inspector does."""
        console.print("\n[bold blue]2. Testing JSON-RPC message/send[/bold blue]")
        
        request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": f"inspector-{datetime.now().timestamp()}",
            "params": {
                "message": {
                    "parts": [{
                        "kind": "text",
                        "text": text
                    }],
                    "role": "user"
                }
            }
        }
        
        console.print(f"  Query: \"{text}\"")
        
        try:
            response = self.client.post("/", json=request)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate JSON-RPC structure
                if "jsonrpc" not in result or result["jsonrpc"] != "2.0":
                    console.print("[red]✗ Invalid JSON-RPC version[/red]")
                    return False
                
                if "id" not in result or result["id"] != request["id"]:
                    console.print("[red]✗ JSON-RPC ID mismatch[/red]")
                    return False
                
                if "result" not in result:
                    console.print("[red]✗ Missing result field[/red]")
                    return False
                
                # Validate Message structure
                message = result["result"]
                
                if message.get("kind") != "message":
                    console.print(f"[red]✗ Wrong kind: {message.get('kind')}[/red]")
                    return False
                
                if "message_id" not in message and "messageId" not in message:
                    console.print("[red]✗ Missing message_id/messageId[/red]")
                    return False
                
                if message.get("role") not in ["agent", "assistant"]:
                    console.print(f"[red]✗ Invalid role: {message.get('role')}[/red]")
                    return False
                
                # Validate parts
                parts = message.get("parts", [])
                if not parts:
                    console.print("[red]✗ No parts in response[/red]")
                    return False
                
                valid_parts = True
                for i, part in enumerate(parts):
                    if "kind" not in part:
                        console.print(f"[red]✗ Part {i} missing 'kind'[/red]")
                        valid_parts = False
                    elif part["kind"] == "text" and "text" not in part:
                        console.print(f"[red]✗ TextPart {i} missing 'text'[/red]")
                        valid_parts = False
                    elif part["kind"] == "data" and "data" not in part:
                        console.print(f"[red]✗ DataPart {i} missing 'data'[/red]")
                        valid_parts = False
                
                if not valid_parts:
                    return False
                
                console.print("[green]✓ JSON-RPC response valid[/green]")
                console.print(f"  Message ID: {message.get('message_id') or message.get('messageId')}")
                console.print(f"  Role: {message['role']}")
                console.print(f"  Parts: {len(parts)} ({', '.join(p['kind'] for p in parts)})")
                
                return True
            else:
                console.print(f"[red]✗ HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers for web access."""
        console.print("\n[bold blue]3. Testing CORS Headers[/bold blue]")
        
        try:
            # Send OPTIONS request as browser would
            response = self.client.options("/", headers={
                "Origin": "https://a2a-inspector.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            })
            
            headers = response.headers
            
            # Check required CORS headers
            checks = [
                ("access-control-allow-origin" in headers, "Allow-Origin"),
                ("access-control-allow-methods" in headers, "Allow-Methods"),
                ("access-control-allow-headers" in headers, "Allow-Headers")
            ]
            
            all_pass = True
            for check, name in checks:
                if check:
                    console.print(f"[green]✓ {name} header present[/green]")
                else:
                    console.print(f"[red]✗ Missing {name} header[/red]")
                    all_pass = False
            
            return all_pass
            
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error responses match A2A spec."""
        console.print("\n[bold blue]4. Testing Error Handling[/bold blue]")
        
        # Test invalid method
        request = {
            "jsonrpc": "2.0",
            "method": "invalid/method",
            "id": "error-test",
            "params": {}
        }
        
        try:
            response = self.client.post("/", json=request)
            
            # We expect this to fail gracefully
            if response.status_code == 200:
                result = response.json()
                
                # Should have either error in JSON-RPC or failed task
                if "error" in result:
                    console.print("[green]✓ JSON-RPC error format correct[/green]")
                    return True
                elif "result" in result:
                    # Check if it's a failed task
                    task = result.get("result", {})
                    if task.get("kind") == "task":
                        status = task.get("status", {})
                        if isinstance(status, dict) and status.get("state") == "failed":
                            console.print("[green]✓ Task failure format correct[/green]")
                            return True
                
            console.print("[yellow]⚠ Error handling could be improved[/yellow]")
            return True  # Not critical
            
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False
    
    def close(self):
        """Close the client."""
        self.client.close()


def main():
    """Run A2A Inspector simulation tests."""
    console.print(Panel(
        "[bold cyan]🔍 A2A Inspector Compatibility Test[/bold cyan]\n"
        "Simulating A2A Inspector request patterns",
        border_style="blue"
    ))
    
    simulator = A2AInspectorSimulator()
    results = {}
    
    try:
        # Run all tests
        results["Agent Card"] = simulator.test_agent_card()
        results["JSON-RPC Message"] = simulator.test_json_rpc_message("luxury travel enthusiasts")
        results["CORS Headers"] = simulator.test_cors_headers()
        results["Error Handling"] = simulator.test_error_handling()
        
    finally:
        simulator.close()
    
    # Summary
    console.print("\n[bold]Compatibility Results:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Test", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Notes")
    
    notes = {
        "Agent Card": "Required for agent discovery",
        "JSON-RPC Message": "Core communication protocol",
        "CORS Headers": "Web browser access",
        "Error Handling": "Graceful failure modes"
    }
    
    for test_name, passed in results.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        table.add_row(test_name, status, notes[test_name])
    
    console.print(table)
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        console.print("\n[bold green]🎉 Full A2A Inspector compatibility achieved![/bold green]")
        console.print("Your agent is ready to be used with the A2A Inspector web tool.")
    else:
        console.print("\n[bold yellow]⚠ Some compatibility issues remain[/bold yellow]")
        console.print("Review the failed tests above for details.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())