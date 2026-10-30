import logging
from schemas import ToolExecutionRequest, TransactionEvaluation
from checkpoint import StateCheckpointManager
from database import init_db, log_transaction

logger = logging.getLogger("ResilientRestore")
logger.setLevel(logging.INFO)

class ResilientRestoreMiddleware:
    def __init__(self):
        self.manager = StateCheckpointManager()
        init_db()  # Ensure database and table exist

    def execute_transaction(self, request: ToolExecutionRequest, tool_callable) -> TransactionEvaluation:
        logger.info(f"Initiating transactional execution for tool: {request.tool_name}")
        
        # 1. Take pre-execution snapshot if target path is provided
        tx_id = self.manager.create_snapshot(request.target_path)
        
        try:
            # 2. Execute tool execution logic
            result = tool_callable(request.arguments)
            
            # If tool signals failure or raises exception
            if isinstance(result, dict) and result.get("status") == "error":
                raise RuntimeError(result.get("reason", "Unknown execution failure"))
                
            if tx_id:
                self.manager.commit(tx_id)
                
            eval_res = TransactionEvaluation(
                status="COMMITTED",
                transaction_id=tx_id or "no_state_change",
                message="Tool executed successfully and state committed."
            )
            
            # Log to SQLite
            log_transaction(eval_res.transaction_id, request.tool_name, request.target_path, eval_res.status)
            return eval_res
            
        except Exception as e:
            logger.warning(f"Execution failed: {str(e)}. Triggering automated rollback...")
            if tx_id:
                self.manager.rollback(tx_id)
                
            eval_res = TransactionEvaluation(
                status="ROLLED_BACK",
                transaction_id=tx_id or "no_state_change",
                message="Tool execution failed. State successfully restored via snapshot.",
                error_detail=str(e)
            )
            
            # Log failure and rollback to SQLite
            log_transaction(eval_res.transaction_id, request.tool_name, request.target_path, eval_res.status, str(e))
            return eval_res