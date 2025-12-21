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
    assert resume_data["result"]["task"]["id"] == task.id
