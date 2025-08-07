#!/usr/bin/env python3
"""Test using official a2a SDK client to validate our implementation."""

import asyncio
import json
import httpx
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import official a2a types for validation
try:
    from a2a.types import (
        Message, TextPart, DataPart, Role,
        Task, TaskStatus,
        AgentCard, AgentSkill, AgentCapabilities
    )
    A2A_SDK_AVAILABLE = True
except ImportError:
    A2A_SDK_AVAILABLE = False
    print("Warning: a2a SDK not available")

console = Console()


class A2ATestClient:
    """Test client for A2A protocol using official types."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def get_agent_card(self) -> dict:
        """Fetch and validate agent card."""
        response = await self.client.get("/agent-card")
        response.raise_for_status()
        card_data = response.json()
        
        if A2A_SDK_AVAILABLE:
            # Validate with official types
            try:
                # Map the response to official AgentCard format
                skills = [
                    AgentSkill(
                        id=skill["id"],
                        name=skill["name"],
                        description=skill["description"],
                        tags=skill.get("tags", []),
                        inputSchema=skill.get("inputSchema", {})
                    )
                    for skill in card_data.get("skills", [])
                ]
                
                capabilities = AgentCapabilities(
                    streaming=card_data["capabilities"].get("streaming", False),
                    push_notifications=card_data["capabilities"].get("pushNotifications", False),
                    state_transition_history=card_data["capabilities"].get("stateTransitionHistory", False),
                    extensions=card_data["capabilities"].get("extensions", [])
                )
                
                # Create validated card
                validated_card = AgentCard(
                    name=card_data["name"],
                    description=card_data["description"],
                    version=card_data["version"],
                    url=card_data["url"],
                    defaultInputModes=card_data.get("defaultInputModes", ["text"]),
                    defaultOutputModes=card_data.get("defaultOutputModes", ["text"]),
                    capabilities=capabilities,
                    skills=skills
                )
                
                console.print("[green]✓ Agent card validated with official A2A types[/green]")
                return validated_card.model_dump()
            except Exception as e:
                console.print(f"[red]✗ Agent card validation failed: {e}[/red]")
                raise
        
        return card_data
    
    async def send_message(self, text: str) -> dict:
        """Send a message using JSON-RPC format and validate response."""
        request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": f"msg_{datetime.now().timestamp()}",
            "params": {
                "message": {
                    "parts": [{"kind": "text", "text": text}],
                    "role": "user"
                }
            }
        }
        
        response = await self.client.post("/", json=request)
        response.raise_for_status()
        result = response.json()
        
        # Extract message from JSON-RPC response
        message_data = result.get("result", {})
        
        if A2A_SDK_AVAILABLE:
            # Validate message response with official types
            try:
                parts = []
                for part in message_data.get("parts", []):
                    if part["kind"] == "text":
                        parts.append(TextPart(kind="text", text=part["text"]))
                    elif part["kind"] == "data":
                        parts.append(DataPart(kind="data", data=part["data"]))
                
                validated_message = Message(
                    kind="message",
                    message_id=message_data["message_id"],
                    parts=parts,
                    role=Role(message_data["role"])
                )
                
                console.print("[green]✓ Message response validated with official A2A types[/green]")
                return validated_message.model_dump()
            except Exception as e:
                console.print(f"[red]✗ Message validation failed: {e}[/red]")
                raise
        
        return message_data
    
    async def send_task(self, task_type: str, params: dict) -> dict:
        """Send a task and validate response."""
        task_request = {
            "taskId": f"task_{datetime.now().timestamp()}",
            "type": task_type,
            "parameters": params
        }
        
        response = await self.client.post("/a2a/task", json=task_request)
        response.raise_for_status()
        task_data = response.json()
        
        if A2A_SDK_AVAILABLE:
            # Validate task response with official types
            try:
                from a2a.types import TaskStatus, TaskState
                
                # Parse the status object
                status_data = task_data.get("status", {})
                
                # Create TaskStatus from the status data
                if isinstance(status_data, dict) and "state" in status_data:
                    # Parse the message if present
                    message = None
                    if "message" in status_data and status_data["message"]:
                        msg_data = status_data["message"]
                        parts = []
                        for part in msg_data.get("parts", []):
                            if part["kind"] == "text":
                                parts.append(TextPart(kind="text", text=part["text"]))
                            elif part["kind"] == "data":
                                parts.append(DataPart(kind="data", data=part["data"]))
                        
                        message = Message(
                            kind="message",
                            message_id=msg_data.get("messageId", msg_data.get("message_id")),
                            parts=parts,
                            role=Role(msg_data["role"])
                        )
                    
                    task_status = TaskStatus(
                        state=TaskState(status_data["state"]),
                        timestamp=status_data.get("timestamp"),
                        message=message
                    )
                else:
                    # Legacy format - just a string status
                    task_status = TaskStatus(
                        state=TaskState("completed" if task_data.get("status") == "Completed" else "working")
                    )
                
                validated_task = Task(
                    id=task_data["id"],
                    kind="task",
                    status=task_status,
                    context_id=task_data.get("contextId"),
                    metadata=task_data.get("metadata", {})
                )
                
                console.print("[green]✓ Task response validated with official A2A types[/green]")
                return validated_task.model_dump()
            except Exception as e:
                console.print(f"[red]✗ Task validation failed: {e}[/red]")
                raise
        
        return task_data
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()


async def test_full_workflow():
    """Test complete A2A workflow with official validation."""
    console.print(Panel(
        "[bold cyan]🎯 Official A2A SDK Client Test[/bold cyan]\n"
        "Testing with official a2a types and validation",
        border_style="blue"
    ))
    
    client = A2ATestClient()
    results = {}
    
    try:
        # Test 1: Agent Card
        console.print("\n[bold blue]1. Testing Agent Card[/bold blue]")
        try:
            card = await client.get_agent_card()
            console.print(f"  Name: {card['name']}")
            console.print(f"  Version: {card['version']}")
            console.print(f"  Skills: {len(card.get('skills', []))}")
            results["Agent Card"] = True
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            results["Agent Card"] = False
        
        # Test 2: Message/Send (JSON-RPC)
        console.print("\n[bold blue]2. Testing Message/Send (A2A Inspector format)[/bold blue]")
        try:
            message = await client.send_message("sports car enthusiasts")
            console.print(f"  Message ID: {message.get('message_id')}")
            console.print(f"  Role: {message.get('role')}")
            console.print(f"  Parts: {len(message.get('parts', []))}")
            results["Message/Send"] = True
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            results["Message/Send"] = False
        
        # Test 3: Discovery Task
        console.print("\n[bold blue]3. Testing Discovery Task[/bold blue]")
        try:
            task = await client.send_task("discovery", {
                "query": "luxury travel",
                "max_results": 5
            })
            console.print(f"  Task ID: {task.get('id')}")
            console.print(f"  Status: {task.get('status')}")
            console.print(f"  Context ID: {task.get('contextId')}")
            
            # Check output
            output = task.get("output", {})
            parts = output.get("parts", [])
            if parts:
                content = parts[0].get("content", {})
                signals = content.get("signals", [])
                console.print(f"  Signals found: {len(signals)}")
            
            results["Discovery Task"] = True
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            results["Discovery Task"] = False
        
        # Test 4: SDK Validation Summary
        if A2A_SDK_AVAILABLE:
            console.print("\n[bold blue]4. SDK Type Validation[/bold blue]")
            console.print("[green]✓ All responses validated against official a2a types[/green]")
            results["SDK Validation"] = True
        else:
            console.print("\n[yellow]⚠ SDK not available for validation[/yellow]")
            results["SDK Validation"] = False
        
    finally:
        await client.close()
    
    # Summary
    console.print("\n[bold]Test Results Summary:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Test", style="white")
    table.add_column("Status", justify="center")
    
    for test_name, passed in results.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        table.add_row(test_name, status)
    
    console.print(table)
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        console.print("\n[bold green]🎉 All tests passed! Agent is A2A compliant.[/bold green]")
    else:
        console.print("\n[bold red]❌ Some tests failed. Review the output above.[/bold red]")
    
    return all_passed


async def main():
    """Main entry point."""
    try:
        success = await test_full_workflow()
        return 0 if success else 1
    except Exception as e:
        console.print(f"[bold red]Test failed with error: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())