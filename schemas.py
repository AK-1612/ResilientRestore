from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional, Literal

class ToolExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    
    tool_name: str = Field(..., description="Target tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    target_path: Optional[str] = Field(None, description="Optional target file path for snapshot checkpointing")

class TransactionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    
    status: Literal["COMMITTED", "ROLLED_BACK", "FAILED"]
    transaction_id: str
    message: str
    error_detail: Optional[str] = None