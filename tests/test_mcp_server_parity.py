import json

from core.desktop.devtools.interface.mcp_server import MCPServer, JsonRpcRequest


def _init_server(server: MCPServer):
    server.handle_request(JsonRpcRequest(jsonrpc="2.0", method="initialize", id=1, params={}))
    server.handle_request(JsonRpcRequest(jsonrpc="2.0", method="notifications/initialized", id=None, params={}))


def _parse_content(content: dict) -> dict:
    """Parse MCP content entry. Supports both text (standard) and json (legacy) types."""
    if content["type"] == "text":
        return json.loads(content["text"])
    elif content["type"] == "json":
        return content["json"]
    raise ValueError(f"Unsupported content type: {content['type']}")


def test_mcp_returns_text_content(monkeypatch, tmp_path):
    server = MCPServer(tasks_dir=tmp_path, use_global=False)
    _init_server(server)

    tools_resp = server.handle_request(JsonRpcRequest(
        jsonrpc="2.0",
        method="tools/list",
        id=0,
        params={},
    ))
    tools = (tools_resp or {}).get("result", {}).get("tools", [])
    close_tool = next((t for t in tools if t.get("name") == "tasks_close_task"), None)
    assert close_tool is not None
    close_props = ((close_tool.get("inputSchema") or {}).get("properties") or {})
    assert (close_props.get("compact") or {}).get("default") is True

    # create a sample plan + task
    manager = server.manager
    plan = manager.create_plan("Plan")
    manager.save_task(plan, skip_sync=True)
    task = manager.create_task("Sample", parent=plan.id)
    manager.save_task(task, skip_sync=True)

    # context (include_all)
    ctx_resp = server.handle_request(JsonRpcRequest(
        jsonrpc="2.0",
        method="tools/call",
        id=2,
        params={"name": "tasks_context", "arguments": {"include_all": True}},
    ))
    content = ctx_resp["result"]["content"][0]
    assert content["type"] == "text"
    ctx_data = _parse_content(content)
    assert any(t["id"] == task.id for t in ctx_data["result"]["tasks"])

    # resume
    resume_resp = server.handle_request(JsonRpcRequest(
        jsonrpc="2.0",
        method="tools/call",
        id=3,
        params={"name": "tasks_resume", "arguments": {"task": task.id}},
    ))
    resume_content = resume_resp["result"]["content"][0]
    assert resume_content["type"] == "text"
    resume_data = _parse_content(resume_content)
    assert resume_data["result"]["summary"]["focus"]["id"] == task.id
    # compact=true is the default: resume returns a short summary strip unless explicitly requested
    assert "task" not in (resume_data["result"] or {})

    # patch(dry_run) preview must include trust-by-diff fields and current/after snapshots
    patch_resp = server.handle_request(JsonRpcRequest(
        jsonrpc="2.0",
        method="tools/call",
        id=4,
        params={
            "name": "tasks_patch",
            "arguments": {
                "task": task.id,
                "dry_run": True,
                "ops": [{"op": "append", "field": "success_criteria", "value": "done"}],
            },
        },
    ))
    patch_content = patch_resp["result"]["content"][0]
    assert patch_content["type"] == "text"
    patch_data = _parse_content(patch_content)
    result = patch_data["result"]
    assert result.get("dry_run") is True
    assert result.get("kind") == "task_detail"
    assert "diff" in result
    assert (result.get("diff") or {}).get("fields"), "patch(dry_run) must return non-empty diff.fields for changes"
    assert "current" in result and "after" in result
    # compact previews are state+diff; full snapshots require compact=false
    assert "task" not in (result.get("current") or {})
    assert "task" not in (result.get("after") or {})

    # close_task(dry_run) preview must return applyable diff.patches derived from runway.recipe
    close_resp = server.handle_request(JsonRpcRequest(
        jsonrpc="2.0",
        method="tools/call",
        id=5,
        params={"name": "tasks_close_task", "arguments": {"task": task.id, "apply": False}},
    ))
    close_content = close_resp["result"]["content"][0]
    assert close_content["type"] == "text"
    close_data = _parse_content(close_content)
    diff = ((close_data.get("result") or {}).get("diff") or {})
    patches = diff.get("patches") or []
    assert len(patches) == 1
    assert patches[0].get("kind") == "task_detail"
