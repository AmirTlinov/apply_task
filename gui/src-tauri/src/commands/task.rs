//! Task-related Tauri commands
//!
//! These commands are invoked from the React frontend via Tauri's invoke API.

use serde_json::{json, Value};
use tauri::State;

use crate::AppState;

/// Backend storage mode response
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct BackendStorageModeResponse {
    pub success: bool,
    pub mode: String,
    pub restarted: bool,
    pub error: Option<String>,
}

fn bridge_error(intent: &str, message: String) -> Value {
    json!({
        "success": false,
        "intent": intent,
        "result": {},
        "warnings": [],
        "context": {},
        "suggestions": [],
        "meta": {},
        "error": { "code": "BRIDGE_ERROR", "message": message },
        "timestamp": ""
    })
}

/// Execute AI intent (transparent proxy to MCP tools: tasks_<intent>)
#[tauri::command]
pub async fn ai_intent(
    state: State<'_, AppState>,
    intent: String,
    params: Option<Value>,
) -> Result<Value, String> {
    let bridge = state.bridge.lock().await;

    let normalized_intent = intent.trim().to_lowercase();
    let tool_name = format!("tasks_{}", normalized_intent);

    let request_params = params.unwrap_or(json!({}));

    match bridge.invoke(&tool_name, Some(request_params)).await {
        Ok(result) => Ok(result),
        Err(e) => Ok(bridge_error(&normalized_intent, e.to_string())),
    }
}

#[tauri::command]
pub async fn backend_set_storage_mode(
    state: State<'_, AppState>,
    mode: String,
) -> Result<BackendStorageModeResponse, String> {
    let bridge = state.bridge.lock().await;

    match bridge.set_storage_mode(&mode).await {
        Ok(restarted) => Ok(BackendStorageModeResponse {
            success: true,
            mode: bridge.storage_mode_str().to_string(),
            restarted,
            error: None,
        }),
        Err(e) => Ok(BackendStorageModeResponse {
            success: false,
            mode,
            restarted: false,
            error: Some(e.to_string()),
        }),
    }
}
