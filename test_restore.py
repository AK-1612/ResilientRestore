import pytest
import os
from schemas import ToolExecutionRequest
from middleware import ResilientRestoreMiddleware

@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test_state.txt"
    f.write_text("INITIAL_SECURE_STATE")
    return str(f)

def test_successful_commit(temp_file):
    middleware = ResilientRestoreMiddleware()
    req = ToolExecutionRequest(
        tool_name="file_editor",
        arguments={"write_data": "UPDATED_STATE", "file_path": temp_file},
        target_path=temp_file
    )
    
    def dummy_tool(args):
        with open(args["file_path"], "w") as f:
            f.write(args["write_data"])
        return {"status": "success"}

    eval_res = middleware.execute_transaction(req, dummy_tool)
    assert eval_res.status == "COMMITTED"
    assert open(temp_file).read() == "UPDATED_STATE"

def test_automatic_rollback_on_failure(temp_file):
    middleware = ResilientRestoreMiddleware()
    req = ToolExecutionRequest(
        tool_name="file_editor",
        arguments={"command": "fail", "file_path": temp_file},
        target_path=temp_file
    )
    
    def failing_tool(args):
        with open(args["file_path"], "w") as f:
            f.write("CORRUPTED_DATA")
        raise RuntimeError("Agent failed midway.")

    eval_res = middleware.execute_transaction(req, failing_tool)
    assert eval_res.status == "ROLLED_BACK"
    # State should revert back to original snapshot
    assert open(temp_file).read() == "INITIAL_SECURE_STATE"