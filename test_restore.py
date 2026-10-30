import pytest
import os
import sqlite3
from schemas import ToolExecutionRequest
from middleware import ResilientRestoreMiddleware
from database import DB_NAME, init_db

@pytest.fixture(autouse=True)
def clean_db():
    """Ensures a clean database state before each test."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM audit_logs")
    conn.commit()
    conn.close()

@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "enterprise_state.txt"
    f.write_text("INITIAL_SECURE_STATE")
    return str(f)

def test_successful_commit_and_db_audit(temp_file):
    middleware = ResilientRestoreMiddleware()
    req = ToolExecutionRequest(
        tool_name="enterprise_file_editor",
        arguments={"write_data": "UPDATED_SECURE_STATE", "file_path": temp_file},
        target_path=temp_file
    )
    
    def dummy_tool(args):
        with open(args["file_path"], "w") as f:
            f.write(args["write_data"])
        return {"status": "success"}

    # Execute transaction
    eval_res = middleware.execute_transaction(req, dummy_tool)
    
    # Assertions on execution result
    assert eval_res.status == "COMMITTED"
    assert open(temp_file).read() == "UPDATED_SECURE_STATE"

    # REAL DB TEST: Verify entry in SQLite audit log
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs WHERE transaction_id = ?", (eval_res.transaction_id,))
    log_row = cursor.fetchone()
    conn.close()

    assert log_row is not None
    assert log_row["tool_name"] == "enterprise_file_editor"
    assert log_row["status"] == "COMMITTED"
    assert log_row["target_path"] == temp_file
    assert log_row["error_detail"] is None
    print(f"\n[Verified DB Audit]: Transaction {log_row['transaction_id']} successfully recorded as COMMITTED.")

def test_automatic_rollback_and_db_audit(temp_file):
    middleware = ResilientRestoreMiddleware()
    req = ToolExecutionRequest(
        tool_name="enterprise_file_editor",
        arguments={"command": "fail", "file_path": temp_file},
        target_path=temp_file
    )
    
    def failing_tool(args):
        with open(args["file_path"], "w") as f:
            f.write("MALICIOUS_CORRUPTION")
        raise RuntimeError("Agent hallucination / execution crash mid-workflow.")

    # Execute transaction
    eval_res = middleware.execute_transaction(req, failing_tool)
    
    # Assertions on state rollback
    assert eval_res.status == "ROLLED_BACK"
    assert open(temp_file).read() == "INITIAL_SECURE_STATE"

    # REAL DB TEST: Verify entry in SQLite audit log captures the failure and error detail
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs WHERE transaction_id = ?", (eval_res.transaction_id,))
    log_row = cursor.fetchone()
    conn.close()

    assert log_row is not None
    assert log_row["tool_name"] == "enterprise_file_editor"
    assert log_row["status"] == "ROLLED_BACK"
    assert "Agent hallucination" in log_row["error_detail"]
    print(f"\n[Verified DB Audit]: Transaction {log_row['transaction_id']} failure & rollback recorded with error: {log_row['error_detail']}")