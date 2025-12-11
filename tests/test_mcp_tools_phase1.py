"""Unit tests for Phase 1 MCP tool definitions.

Tests the two new MCP tools for Phase 1 functionality:
- tasks_note: Add progress notes to subtasks
- tasks_block: Block/unblock subtasks

These tools are defined in mcp_server.py and map to intents
that will be implemented in Unit 6.
"""
import pytest
from core.desktop.devtools.interface.mcp_server import (
    get_tool_definitions,
    TOOL_TO_INTENT,
)


class TestTasksNoteTool:
    """Test tasks_note tool definition."""

    def test_tasks_note_tool_exists(self):
        """Verify tasks_note tool exists in definitions."""
        tools = get_tool_definitions()
        tool_names = [tool["name"] for tool in tools]
        assert "tasks_note" in tool_names, "tasks_note tool not found in definitions"

    def test_tasks_note_schema_structure(self):
        """Verify tasks_note tool has correct schema structure."""
        tools = get_tool_definitions()
        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)

        assert note_tool is not None, "tasks_note tool not found"
        assert "description" in note_tool
        assert "inputSchema" in note_tool

        # Check description
        assert "progress note" in note_tool["description"].lower()
        assert "subtask" in note_tool["description"].lower()

        # Check schema structure
        schema = note_tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_tasks_note_required_fields(self):
        """Verify tasks_note has correct required fields."""
        tools = get_tool_definitions()
        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)

        assert note_tool is not None
        required = note_tool["inputSchema"]["required"]

        # Must require: task, path, note
        assert "task" in required
        assert "path" in required
        assert "note" in required
        # Domain should be optional (not in required)
        assert "domain" not in required

    def test_tasks_note_properties(self):
        """Verify tasks_note has all expected properties."""
        tools = get_tool_definitions()
        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)

        assert note_tool is not None
        props = note_tool["inputSchema"]["properties"]

        # Check all properties exist
        assert "task" in props
        assert "path" in props
        assert "domain" in props
        assert "note" in props

        # Check property types
        assert props["task"]["type"] == "string"
        assert props["path"]["type"] == "string"
        assert props["domain"]["type"] == "string"
        assert props["note"]["type"] == "string"

        # Check descriptions
        assert "description" in props["task"]
        assert "description" in props["path"]
        assert "description" in props["domain"]
        assert "description" in props["note"]

        # Check domain default
        assert props["domain"]["default"] == ""

    def test_tasks_note_path_description(self):
        """Verify tasks_note path description includes examples."""
        tools = get_tool_definitions()
        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)

        assert note_tool is not None
        path_desc = note_tool["inputSchema"]["properties"]["path"]["description"]

        # Should mention path format
        assert "path" in path_desc.lower()
        # Should have examples
        assert "0" in path_desc or "subtask" in path_desc.lower()


class TestTasksBlockTool:
    """Test tasks_block tool definition."""

    def test_tasks_block_tool_exists(self):
        """Verify tasks_block tool exists in definitions."""
        tools = get_tool_definitions()
        tool_names = [tool["name"] for tool in tools]
        assert "tasks_block" in tool_names, "tasks_block tool not found in definitions"

    def test_tasks_block_schema_structure(self):
        """Verify tasks_block tool has correct schema structure."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None, "tasks_block tool not found"
        assert "description" in block_tool
        assert "inputSchema" in block_tool

        # Check description
        assert "block" in block_tool["description"].lower()
        assert "subtask" in block_tool["description"].lower()

        # Check schema structure
        schema = block_tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_tasks_block_required_fields(self):
        """Verify tasks_block has correct required fields."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None
        required = block_tool["inputSchema"]["required"]

        # Must require: task, path
        assert "task" in required
        assert "path" in required
        # Optional: domain, blocked, reason
        assert "domain" not in required
        assert "blocked" not in required
        assert "reason" not in required

    def test_tasks_block_properties(self):
        """Verify tasks_block has all expected properties."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None
        props = block_tool["inputSchema"]["properties"]

        # Check all properties exist
        assert "task" in props
        assert "path" in props
        assert "domain" in props
        assert "blocked" in props
        assert "reason" in props

        # Check property types
        assert props["task"]["type"] == "string"
        assert props["path"]["type"] == "string"
        assert props["domain"]["type"] == "string"
        assert props["blocked"]["type"] == "boolean"
        assert props["reason"]["type"] == "string"

        # Check descriptions
        assert "description" in props["task"]
        assert "description" in props["path"]
        assert "description" in props["domain"]
        assert "description" in props["blocked"]
        assert "description" in props["reason"]

    def test_tasks_block_blocked_field(self):
        """Verify tasks_block blocked field has correct config."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None
        blocked_prop = block_tool["inputSchema"]["properties"]["blocked"]

        # Should be boolean type
        assert blocked_prop["type"] == "boolean"
        # Should have default value of True
        assert blocked_prop["default"] is True
        # Should have description explaining true/false
        desc = blocked_prop["description"].lower()
        assert "block" in desc or "unblock" in desc

    def test_tasks_block_reason_optional(self):
        """Verify tasks_block reason field is optional."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None
        required = block_tool["inputSchema"]["required"]

        # Reason should not be required
        assert "reason" not in required

        # But should exist as property
        assert "reason" in block_tool["inputSchema"]["properties"]

        # Should have description mentioning optional
        reason_desc = block_tool["inputSchema"]["properties"]["reason"]["description"]
        assert "optional" in reason_desc.lower()


class TestToolSchemaValidity:
    """Test JSON schema validity for Phase 1 tools."""

    def test_tasks_note_schema_is_valid_json_schema(self):
        """Verify tasks_note schema is valid JSON schema."""
        tools = get_tool_definitions()
        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)

        assert note_tool is not None
        schema = note_tool["inputSchema"]

        # Must have type
        assert "type" in schema
        assert schema["type"] == "object"

        # Must have properties for object type
        assert "properties" in schema
        assert isinstance(schema["properties"], dict)

        # Required must be array
        assert "required" in schema
        assert isinstance(schema["required"], list)

        # All required fields must exist in properties
        for field in schema["required"]:
            assert field in schema["properties"]

    def test_tasks_block_schema_is_valid_json_schema(self):
        """Verify tasks_block schema is valid JSON schema."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None
        schema = block_tool["inputSchema"]

        # Must have type
        assert "type" in schema
        assert schema["type"] == "object"

        # Must have properties for object type
        assert "properties" in schema
        assert isinstance(schema["properties"], dict)

        # Required must be array
        assert "required" in schema
        assert isinstance(schema["required"], list)

        # All required fields must exist in properties
        for field in schema["required"]:
            assert field in schema["properties"]

    def test_all_phase1_properties_have_types(self):
        """Verify all Phase 1 tool properties have type definitions."""
        tools = get_tool_definitions()
        phase1_tools = ["tasks_note", "tasks_block"]

        for tool_name in phase1_tools:
            tool = next((t for t in tools if t["name"] == tool_name), None)
            assert tool is not None, f"{tool_name} not found"

            props = tool["inputSchema"]["properties"]
            for prop_name, prop_def in props.items():
                assert "type" in prop_def, f"{tool_name}.{prop_name} missing type"

    def test_all_phase1_properties_have_descriptions(self):
        """Verify all Phase 1 tool properties have descriptions."""
        tools = get_tool_definitions()
        phase1_tools = ["tasks_note", "tasks_block"]

        for tool_name in phase1_tools:
            tool = next((t for t in tools if t["name"] == tool_name), None)
            assert tool is not None, f"{tool_name} not found"

            props = tool["inputSchema"]["properties"]
            for prop_name, prop_def in props.items():
                assert "description" in prop_def, f"{tool_name}.{prop_name} missing description"
                assert len(prop_def["description"]) > 0, f"{tool_name}.{prop_name} has empty description"


class TestIntentMapping:
    """Test TOOL_TO_INTENT mapping for Phase 1 tools."""

    def test_intent_mapping_note_exists(self):
        """Verify TOOL_TO_INTENT has note mapping."""
        assert "tasks_note" in TOOL_TO_INTENT, "tasks_note not in TOOL_TO_INTENT"

    def test_intent_mapping_note_value(self):
        """Verify tasks_note maps to 'note' intent."""
        assert TOOL_TO_INTENT["tasks_note"] == "note", "tasks_note should map to 'note' intent"

    def test_intent_mapping_block_exists(self):
        """Verify TOOL_TO_INTENT has block mapping."""
        assert "tasks_block" in TOOL_TO_INTENT, "tasks_block not in TOOL_TO_INTENT"

    def test_intent_mapping_block_value(self):
        """Verify tasks_block maps to 'block' intent."""
        assert TOOL_TO_INTENT["tasks_block"] == "block", "tasks_block should map to 'block' intent"

    def test_all_phase1_tools_have_intent_mapping(self):
        """Verify all Phase 1 tools are in TOOL_TO_INTENT."""
        tools = get_tool_definitions()
        phase1_tool_names = ["tasks_note", "tasks_block"]

        for tool_name in phase1_tool_names:
            # Verify tool exists in definitions
            tool = next((t for t in tools if t["name"] == tool_name), None)
            assert tool is not None, f"{tool_name} not found in tool definitions"

            # Verify tool has intent mapping
            assert tool_name in TOOL_TO_INTENT, f"{tool_name} not in TOOL_TO_INTENT"

    def test_intent_mapping_consistency(self):
        """Verify intent mappings are consistent with tool names."""
        # tasks_note should map to note (singular)
        assert TOOL_TO_INTENT["tasks_note"] == "note"

        # tasks_block should map to block (singular)
        assert TOOL_TO_INTENT["tasks_block"] == "block"


class TestPhase1Integration:
    """Integration tests for Phase 1 tools."""

    def test_both_phase1_tools_in_definitions(self):
        """Verify both Phase 1 tools are present in tool definitions."""
        tools = get_tool_definitions()
        tool_names = [tool["name"] for tool in tools]

        assert "tasks_note" in tool_names
        assert "tasks_block" in tool_names

    def test_phase1_tools_have_unique_descriptions(self):
        """Verify Phase 1 tools have distinct descriptions."""
        tools = get_tool_definitions()

        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert note_tool is not None
        assert block_tool is not None

        # Descriptions should be different
        assert note_tool["description"] != block_tool["description"]

        # Note tool should mention notes
        assert "note" in note_tool["description"].lower()

        # Block tool should mention block
        assert "block" in block_tool["description"].lower()

    def test_phase1_tools_share_common_fields(self):
        """Verify Phase 1 tools share common required fields."""
        tools = get_tool_definitions()

        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert note_tool is not None
        assert block_tool is not None

        # Both should require task and path
        assert "task" in note_tool["inputSchema"]["required"]
        assert "path" in note_tool["inputSchema"]["required"]
        assert "task" in block_tool["inputSchema"]["required"]
        assert "path" in block_tool["inputSchema"]["required"]

        # Both should have optional domain
        assert "domain" in note_tool["inputSchema"]["properties"]
        assert "domain" in block_tool["inputSchema"]["properties"]
        assert "domain" not in note_tool["inputSchema"]["required"]
        assert "domain" not in block_tool["inputSchema"]["required"]

    def test_phase1_tools_position_in_list(self):
        """Verify Phase 1 tools are added at the end before return."""
        tools = get_tool_definitions()
        tool_names = [tool["name"] for tool in tools]

        # Find positions
        note_idx = tool_names.index("tasks_note")
        block_idx = tool_names.index("tasks_block")

        # Should be near the end (after tasks_macro_quick)
        quick_idx = tool_names.index("tasks_macro_quick")
        assert note_idx > quick_idx, "tasks_note should be after tasks_macro_quick"
        assert block_idx > quick_idx, "tasks_block should be after tasks_macro_quick"

        # tasks_note should come before tasks_block
        assert note_idx < block_idx, "tasks_note should come before tasks_block"


class TestPhase1Documentation:
    """Test documentation quality for Phase 1 tools."""

    def test_tasks_note_description_clarity(self):
        """Verify tasks_note description is clear and actionable."""
        tools = get_tool_definitions()
        note_tool = next((t for t in tools if t["name"] == "tasks_note"), None)

        assert note_tool is not None
        desc = note_tool["description"]

        # Should mention what it does
        assert "progress note" in desc.lower() or "note" in desc.lower()
        assert "subtask" in desc.lower()

        # Should clarify it doesn't complete
        assert "without" in desc.lower() or "not" in desc.lower() or "complete" not in desc.lower() or "marking it complete" in desc.lower()

    def test_tasks_block_description_clarity(self):
        """Verify tasks_block description is clear and actionable."""
        tools = get_tool_definitions()
        block_tool = next((t for t in tools if t["name"] == "tasks_block"), None)

        assert block_tool is not None
        desc = block_tool["description"]

        # Should mention block/unblock
        assert "block" in desc.lower()
        assert "unblock" in desc.lower() or "or" in desc.lower()

        # Should mention subtask
        assert "subtask" in desc.lower()

        # Should mention optional reason
        assert "optional" in desc.lower() or "reason" in desc.lower()

    def test_phase1_property_descriptions_are_clear(self):
        """Verify all Phase 1 property descriptions are clear."""
        tools = get_tool_definitions()
        phase1_tools = ["tasks_note", "tasks_block"]

        for tool_name in phase1_tools:
            tool = next((t for t in tools if t["name"] == tool_name), None)
            assert tool is not None

            props = tool["inputSchema"]["properties"]
            for prop_name, prop_def in props.items():
                desc = prop_def["description"]
                # Description should be at least 5 characters
                assert len(desc) >= 5, f"{tool_name}.{prop_name} description too short"
                # Description should not be just the field name
                assert desc.lower() != prop_name.lower(), f"{tool_name}.{prop_name} description is just field name"
