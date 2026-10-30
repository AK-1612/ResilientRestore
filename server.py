from fastapi import FastAPI, HTTPException
from schemas import ToolExecutionRequest
from middleware import ResilientRestoreMiddleware
from database import get_all_logs
import os

app = FastAPI(title="ResilientRestore Sidecar", version="1.1.0")
restore_middleware = ResilientRestoreMiddleware()

def mock_tool_executor(arguments: dict):
    command = arguments.get("command", "")
    target_file = arguments.get("file_path")
    
    if "corrupt" in command or "fail" in command:
        if target_file and os.path.exists(target_file):
            with open(target_file, "w") as f:
                f.write("CORRUPTED DATA BY FAILED AGENT")
        raise RuntimeError("Simulated agent tool execution failure.")
        
    if target_file and arguments.get("write_data"):
        with open(target_file, "w") as f:
            f.write(arguments["write_data"])
            
    return {"status": "success"}

@app.post("/api/v1/execute-transactional-tool")
async def execute_transactional_tool(request: ToolExecutionRequest):
    evaluation = restore_middleware.execute_transaction(request, mock_tool_executor)
    
    if evaluation.status == "ROLLED_BACK":
        raise HTTPException(
            status_code=400,
            detail={"transaction_id": evaluation.transaction_id, "reason": evaluation.error_detail}
        )
        
    return {
        "status": "success",
        "transaction_id": evaluation.transaction_id,
        "message": evaluation.message
    }

@app.get("/api/v1/audit-logs")
async def get_audit_logs():
    """Retrieves all immutable transaction audit logs from SQLite."""
    logs = get_all_logs()
    return {
        "total_transactions": len(logs),
        "audit_trail": logs
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)