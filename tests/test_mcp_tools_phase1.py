"""Unit tests for MCP tools: note + block.

Phase 1 UX requires:
- progress notes on step paths (intent=note)
- blocking/unblocking step paths (intent=block)

MCP tools must map 1:1 to canonical intent API intents.
"""

from core.desktop.devtools.interface.mcp_server import get_tool_definitions, TOOL_TO_INTENT


def _tool(name: str) -> dict:
    tools = get_tool_definitions()
    found = next((t for t in tools if t["name"] == name), None)
    assert found is not None, f"{name} tool not found"
    return found


class TestNoteTool:
    def test_tasks_note_exists_and_maps(self):
        assert "tasks_note" in TOOL_TO_INTENT
        assert TOOL_TO_INTENT["tasks_note"] == "note"

    def test_tasks_note_schema(self):
        tool = _tool("tasks_note")
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert set(schema["required"]) == {"task", "path", "note"}

        props = schema["properties"]
        assert props["task"]["type"] == "string"
        assert props["path"]["type"] == "string"
        assert props["note"]["type"] == "string"
        assert props["domain"]["type"] == "string"
        assert props["domain"]["default"] == ""

        desc = tool["description"].lower()
        assert "note" in desc
        assert "progress" in desc


class TestBlockTool:
    def test_tasks_block_exists_and_maps(self):
        assert "tasks_block" in TOOL_TO_INTENT
        assert TOOL_TO_INTENT["tasks_block"] == "block"

    def test_tasks_block_schema(self):
        tool = _tool("tasks_block")
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        # task + path are required; blocked/reason are optional
        assert set(schema["required"]) == {"task", "path"}

        props = schema["properties"]
        assert props["task"]["type"] == "string"
        assert props["path"]["type"] == "string"
        assert props["blocked"]["type"] == "boolean"
        assert props["blocked"]["default"] is True
        assert props["reason"]["type"] == "string"
        assert props["domain"]["type"] == "string"
        assert props["domain"]["default"] == ""

        reason_desc = props["reason"]["description"].lower()
        assert "optional" in reason_desc
