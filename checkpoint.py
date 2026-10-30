import os
import shutil
import uuid
from typing import Dict, Any, Tuple

class StateCheckpointManager:
    def __init__(self, backup_dir: str = ".checkpoints"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        self.active_snapshots: Dict[str, str] = {}

    def create_snapshot(self, target_path: Optional[str]) -> Optional[str]:
        if not target_path or not os.path.exists(target_path):
            return None
        
        tx_id = str(uuid.uuid4())
        backup_path = os.path.join(self.backup_dir, f"{tx_id}_{os.path.basename(target_path)}")
        
        if os.path.isdir(target_path):
            shutil.copytree(target_path, backup_path)
        else:
            shutil.copy2(target_path, backup_path)
            
        self.active_snapshots[tx_id] = (target_path, backup_path)
        return tx_id

    def rollback(self, tx_id: str) -> bool:
        if tx_id not in self.active_snapshots:
            return False
            
        target_path, backup_path = self.active_snapshots[tx_id]
        if os.path.exists(backup_path):
            if os.path.isdir(backup_path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(backup_path, target_path)
                shutil.rmtree(backup_path)
            else:
                shutil.copy2(backup_path, target_path)
                os.remove(backup_path)
                
            del self.active_snapshots[tx_id]
            return True
        return False

    def commit(self, tx_id: str):
        if tx_id in self.active_snapshots:
            _, backup_path = self.active_snapshots[tx_id]
            if os.path.exists(backup_path):
                if os.path.isdir(backup_path):
                    shutil.rmtree(backup_path)
                else:
                    os.remove(backup_path)
            del self.active_snapshots[tx_id]