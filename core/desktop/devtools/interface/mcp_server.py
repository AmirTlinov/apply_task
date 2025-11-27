#!/usr/bin/env python3
"""MCP (Model Context Protocol) stdio server for task management.

Exposes task management functionality as MCP tools for AI assistants.

Usage:
    python -m core.desktop.devtools.interface.mcp_server

Or via the CLI:
    tasks mcp

Configuration for Claude Desktop (~/.config/claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "tasks": {
          "command": "python",
          "args": ["-m", "core.desktop.devtools.interface.mcp_server"],
          "cwd": "/path/to/apply_task"
        }
      }
    }
"""

from __future__ import annotations

import json
import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from core.desktop.devtools.application.task_manager import TaskManager
from core.desktop.devtools.interface.cli_ai import (
    process_intent,
    get_project_tasks_dir,
)
from core.desktop.devtools.interface.tasks_dir_resolver import resolve_project_root
from core.desktop.devtools.interface.ai_state import (
    get_ai_state,
    read_user_signal,
    UserSignal,
)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP PROTOCOL TYPES
# ═══════════════════════════════════════════════════════════════════════════════

MCP_VERSION = "2024-11-05"
SERVER_NAME = "tasks-mcp"
SERVER_VERSION = "1.0.0"


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 request."""
    jsonrpc: str
    method: str
    id: Optional[int | str] = None
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "JsonRpcRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data["method"],
            id=data.get("id"),
            params=data.get("params", {}),
        )


def json_rpc_response(id: Optional[int | str], result: Any) -> Dict:
    """Create JSON-RPC success response."""
    return {"jsonrpc": "2.0", "id": id, "result": result}


def json_rpc_error(id: Optional[int | str], code: int, message: str, data: Any = None) -> Dict:
    """Create JSON-RPC error response."""
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": id, "error": error}


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_tool_definitions() -> List[Dict[str, Any]]:
    """Generate MCP tool definitions from intent handlers."""
    tools = []

    # Context - get current state
    tools.append({
        "name": "tasks_context",
        "description": "Get full context: all tasks, current task state, progress. Use this first to understand the situation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task ID to focus on (optional)"
                },
                "include_all": {
                    "type": "boolean",
                    "description": "Include all tasks list",
                    "default": False
                }
            }
        }
    })

    # Create - create new task
    tools.append({
        "name": "tasks_create",
        "description": "Create a new task with optional subtasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title (required)"
                },
                "description": {
                    "type": "string",
                    "description": "Task description"
                },
                "priority": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "default": "MEDIUM"
                },
                "subtasks": {
                    "type": "array",
                    "description": "Initial subtasks to create",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "criteria": {"type": "array", "items": {"type": "string"}},
                            "tests": {"type": "array", "items": {"type": "string"}},
                            "blockers": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["title"]
                    }
                },
                "idempotency_key": {
                    "type": "string",
                    "description": "Unique key to prevent duplicate creation"
                }
            },
            "required": ["title"]
        }
    })

    # Decompose - add subtasks
    tools.append({
        "name": "tasks_decompose",
        "description": "Break down a task into subtasks with criteria, tests, and blockers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task ID to decompose"
                },
                "subtasks": {
                    "type": "array",
                    "description": "Subtasks to add",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Subtask title"},
                            "criteria": {"type": "array", "items": {"type": "string"}, "description": "Success criteria"},
                            "tests": {"type": "array", "items": {"type": "string"}, "description": "Tests to run"},
                            "blockers": {"type": "array", "items": {"type": "string"}, "description": "Blockers"}
                        },
                        "required": ["title"]
                    }
                },
                "parent": {
                    "type": "string",
                    "description": "Parent subtask path for nesting (e.g., '0' or '0.1')"
                }
            },
            "required": ["task", "subtasks"]
        }
    })

    # Define - set criteria/tests/blockers
    tools.append({
        "name": "tasks_define",
        "description": "Define or update criteria, tests, or blockers for a subtask.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task ID"},
                "path": {"type": "string", "description": "Subtask path (e.g., '0' or '0.1')"},
                "criteria": {"type": "array", "items": {"type": "string"}, "description": "Success criteria"},
                "tests": {"type": "array", "items": {"type": "string"}, "description": "Tests"},
                "blockers": {"type": "array", "items": {"type": "string"}, "description": "Blockers"}
            },
            "required": ["task", "path"]
        }
    })

    # Verify - confirm checkpoints
    tools.append({
        "name": "tasks_verify",
        "description": "Verify that criteria, tests, or blockers are satisfied.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task ID"},
                "path": {"type": "string", "description": "Subtask path"},
                "checkpoints": {
                    "type": "object",
                    "description": "Checkpoints to verify",
                    "properties": {
                        "criteria": {
                            "type": "object",
                            "properties": {
                                "confirmed": {"type": "boolean"},
                                "note": {"type": "string"}
                            }
                        },
                        "tests": {
                            "type": "object",
                            "properties": {
                                "confirmed": {"type": "boolean"},
                                "note": {"type": "string"}
                            }
                        },
                        "blockers": {
                            "type": "object",
                            "properties": {
                                "confirmed": {"type": "boolean"},
                                "note": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "required": ["task", "path", "checkpoints"]
        }
    })

    # Progress - mark subtask complete/incomplete (legacy)
    tools.append({
        "name": "tasks_progress",
        "description": "Mark a subtask as completed or not completed. NOTE: Consider using tasks_done instead for unified completion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task ID"},
                "path": {"type": "string", "description": "Subtask path"},
                "completed": {"type": "boolean", "description": "Completion status", "default": True}
            },
            "required": ["task", "path"]
        }
    })

    # Done - unified completion (auto-verify + mark completed)
    tools.append({
        "name": "tasks_done",
        "description": "Unified completion: auto-verify all checkpoints + mark as completed. Replaces 4 calls (verify×3 + progress) with 1.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task ID"},
                "path": {"type": "string", "description": "Subtask path (e.g., '0' or '0.1')"},
                "note": {"type": "string", "description": "Completion note (optional)"},
                "force": {"type": "boolean", "description": "Force completion even if checkpoints not confirmed", "default": False}
            },
            "required": ["task", "path"]
        }
    })

    # Delete - delete task or subtask
    tools.append({
        "name": "tasks_delete",
        "description": "Delete a task or subtask. If path is provided, deletes subtask; otherwise deletes entire task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task ID"},
                "path": {"type": "string", "description": "Subtask path (optional - if not provided, deletes entire task)"}
            },
            "required": ["task"]
        }
    })

    # Complete - finish task
    tools.append({
        "name": "tasks_complete",
        "description": "Mark the entire task as complete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task ID"},
                "status": {
                    "type": "string",
                    "enum": ["OK", "WARN", "FAIL"],
                    "default": "OK"
                }
            },
            "required": ["task"]
        }
    })

    # Batch - multiple operations
    tools.append({
        "name": "tasks_batch",
        "description": "Execute multiple operations atomically. If atomic=true, all changes are rolled back on any failure.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Default task ID for operations"},
                "atomic": {"type": "boolean", "description": "Rollback all on failure", "default": True},
                "operations": {
                    "type": "array",
                    "description": "Operations to execute",
                    "items": {
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string", "enum": ["decompose", "define", "verify", "progress", "complete"]},
                        },
                        "required": ["intent"]
                    }
                }
            },
            "required": ["operations"]
        }
    })

    # Undo - revert last operation
    tools.append({
        "name": "tasks_undo",
        "description": "Undo the last modifying operation.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    })

    # Redo - redo undone operation
    tools.append({
        "name": "tasks_redo",
        "description": "Redo the last undone operation.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    })

    # History - show operation history
    tools.append({
        "name": "tasks_history",
        "description": "Show recent operation history with undo/redo state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of operations to show", "default": 10}
            }
        }
    })

    # Storage - show storage info
    tools.append({
        "name": "tasks_storage",
        "description": "Show storage information: global/local paths, namespaces.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    })

    # AI Status - get AI session state (for TUI sync)
    tools.append({
        "name": "tasks_ai_status",
        "description": "Get AI session state: current operation, plan progress, statistics. Useful for debugging AI behavior.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    })

    # AI Signal - send signal from user to AI
    tools.append({
        "name": "tasks_user_signal",
        "description": "Read pending user signal (pause, stop, skip, message). AI should check this periodically.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    })

    return tools


# Tool name -> intent mapping
TOOL_TO_INTENT = {
    "tasks_context": "context",
    "tasks_create": "create",
    "tasks_decompose": "decompose",
    "tasks_define": "define",
    "tasks_verify": "verify",
    "tasks_progress": "progress",
    "tasks_done": "done",  # NEW: unified completion
    "tasks_delete": "delete",  # NEW: delete task/subtask
    "tasks_complete": "complete",
    "tasks_batch": "batch",
    "tasks_undo": "undo",
    "tasks_redo": "redo",
    "tasks_history": "history",
    "tasks_storage": "storage",
    # Special tools (handled directly, not via intent)
    "tasks_ai_status": "_ai_status",
    "tasks_user_signal": "_user_signal",
}


# ═══════════════════════════════════════════════════════════════════════════════
# MCP SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class MCPServer:
    """MCP stdio server for task management."""

    def __init__(self, tasks_dir: Optional[Path] = None, use_global: bool = True):
        if tasks_dir:
            self.tasks_dir = tasks_dir
        else:
            self.tasks_dir = get_project_tasks_dir(resolve_project_root(), use_global=use_global)

        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.manager = TaskManager(tasks_dir=self.tasks_dir)
        self._initialized = False

    def handle_request(self, request: JsonRpcRequest) -> Dict:
        """Handle a single JSON-RPC request."""
        method = request.method
        params = request.params

        # Initialize
        if method == "initialize":
            return self._handle_initialize(request.id, params)

        # Check initialized
        if not self._initialized and method != "notifications/initialized":
            return json_rpc_error(request.id, -32002, "Server not initialized")

        # Route methods
        if method == "notifications/initialized":
            self._initialized = True
            return None  # No response for notifications

        elif method == "tools/list":
            return self._handle_tools_list(request.id)

        elif method == "tools/call":
            return self._handle_tools_call(request.id, params)

        elif method == "ping":
            return json_rpc_response(request.id, {})

        else:
            return json_rpc_error(request.id, -32601, f"Method not found: {method}")

    def _handle_initialize(self, id: Optional[int | str], params: Dict) -> Dict:
        """Handle initialize request."""
        return json_rpc_response(id, {
            "protocolVersion": MCP_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
            "capabilities": {
                "tools": {},
            }
        })

    def _handle_tools_list(self, id: Optional[int | str]) -> Dict:
        """Handle tools/list request."""
        return json_rpc_response(id, {
            "tools": get_tool_definitions()
        })

    def _handle_tools_call(self, id: Optional[int | str], params: Dict) -> Dict:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in TOOL_TO_INTENT:
            return json_rpc_error(id, -32602, f"Unknown tool: {tool_name}")

        intent = TOOL_TO_INTENT[tool_name]

        # Handle special tools directly
        if intent == "_ai_status":
            return self._handle_ai_status(id)
        elif intent == "_user_signal":
            return self._handle_user_signal(id)

        # Build intent request
        intent_data = {"intent": intent, **arguments}

        # Process through cli_ai
        try:
            response = process_intent(self.manager, intent_data)

            # Format as MCP tool result
            result_content = {
                "success": response.success,
                "result": response.result,
                "context": response.context,
                "suggestions": [s.to_dict() for s in response.suggestions],
            }

            if response.meta:
                result_content["meta"] = response.meta.to_dict()

            if response.error:
                result_content["error"] = response.error.to_dict()

            return json_rpc_response(id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_content, ensure_ascii=False, indent=2)
                    }
                ],
                "isError": not response.success
            })

        except Exception as e:
            return json_rpc_response(id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"error": str(e)}, ensure_ascii=False)
                    }
                ],
                "isError": True
            })

    def _handle_ai_status(self, id: Optional[int | str]) -> Dict:
        """Handle tasks_ai_status tool call."""
        ai_state = get_ai_state()
        result = ai_state.to_dict()

        return json_rpc_response(id, {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ],
            "isError": False
        })

    def _handle_user_signal(self, id: Optional[int | str]) -> Dict:
        """Handle tasks_user_signal tool call."""
        signal, message = read_user_signal(self.tasks_dir)

        result = {
            "signal": signal.value,
            "message": message,
            "has_signal": signal != UserSignal.NONE,
        }

        # Add hint for what to do with the signal
        if signal == UserSignal.PAUSE:
            result["action"] = "Pause execution, wait for resume"
        elif signal == UserSignal.STOP:
            result["action"] = "Stop current task execution"
        elif signal == UserSignal.SKIP:
            result["action"] = "Skip current subtask and move to next"
        elif signal == UserSignal.MESSAGE:
            result["action"] = f"User message: {message}"

        return json_rpc_response(id, {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ],
            "isError": False
        })


def run_stdio_server(tasks_dir: Optional[Path] = None, use_global: bool = True):
    """Run MCP server over stdio."""
    server = MCPServer(tasks_dir=tasks_dir, use_global=use_global)

    # Read from stdin, write to stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            request = JsonRpcRequest.from_dict(data)
            response = server.handle_request(request)

            if response is not None:  # Notifications don't get responses
                print(json.dumps(response), flush=True)

        except json.JSONDecodeError as e:
            error = json_rpc_error(None, -32700, f"Parse error: {e}")
            print(json.dumps(error), flush=True)
        except Exception as e:
            error = json_rpc_error(None, -32603, f"Internal error: {e}")
            print(json.dumps(error), flush=True)


async def run_stdio_server_async(tasks_dir: Optional[Path] = None, use_global: bool = True):
    """Run MCP server over stdio (async version)."""
    server = MCPServer(tasks_dir=tasks_dir, use_global=use_global)

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)

    while True:
        try:
            line = await reader.readline()
            if not line:
                break

            line = line.decode().strip()
            if not line:
                continue

            data = json.loads(line)
            request = JsonRpcRequest.from_dict(data)
            response = server.handle_request(request)

            if response is not None:
                output = json.dumps(response) + "\n"
                writer.write(output.encode())
                await writer.drain()

        except json.JSONDecodeError as e:
            error = json_rpc_error(None, -32700, f"Parse error: {e}")
            writer.write((json.dumps(error) + "\n").encode())
            await writer.drain()
        except Exception as e:
            error = json_rpc_error(None, -32603, f"Internal error: {e}")
            writer.write((json.dumps(error) + "\n").encode())
            await writer.drain()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP stdio server for task management")
    parser.add_argument("--tasks-dir", type=Path, help="Tasks directory")
    parser.add_argument("--local", action="store_true", help="Use local .tasks instead of global")
    parser.add_argument("--async", dest="use_async", action="store_true", help="Use async mode")

    args = parser.parse_args()

    if args.use_async:
        asyncio.run(run_stdio_server_async(
            tasks_dir=args.tasks_dir,
            use_global=not args.local
        ))
    else:
        run_stdio_server(
            tasks_dir=args.tasks_dir,
            use_global=not args.local
        )


if __name__ == "__main__":
    main()
