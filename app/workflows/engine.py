"""
Workflow execution engine with dependency resolution and parallel execution
"""
from typing import Dict, List, Set, Any
from PyQt5.QtCore import QThread, pyqtSignal
import json
from datetime import datetime
import time

from app.workflows.schemas import WorkflowDefinition, TaskResult, TaskStatus
from app.tools.registry import ToolRegistry
from app.core.database import SessionLocal, Scan, Task

class WorkflowWorker(QThread):
    """Worker thread for executing workflows"""
    
    task_started = pyqtSignal(str, str)  # task_id, task_name
    task_completed = pyqtSignal(str, dict)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error
    workflow_completed = pyqtSignal(dict)  # final results
    progress_updated = pyqtSignal(int)  # progress percentage
    
    def __init__(self, workflow: WorkflowDefinition, user_id: int):
        super().__init__()
        self.workflow = workflow
        self.user_id = user_id
        self.tool_registry = ToolRegistry()
        self.task_results: Dict[str, TaskResult] = {}
        self.scan_id = None
        self._stop_requested = False
        
    def run(self):
        """Execute the workflow"""
        try:
            # Create scan record
            db = SessionLocal()
            scan = Scan(
                user_id=self.user_id,
                workflow_name=self.workflow.name,
                target=self.workflow.target,
                status="running"
            )
            db.add(scan)
            db.commit()
            self.scan_id = scan.id
            db.close()
            
            # Execute workflow
            self._execute_workflow()
            
            # Mark as completed
            db = SessionLocal()
            scan = db.query(Scan).filter(Scan.id == self.scan_id).first()
            scan.status = "completed" if not self._stop_requested else "cancelled"
            scan.completed_at = datetime.utcnow()
            scan.results = json.dumps({
                task_id: result.dict() 
                for task_id, result in self.task_results.items()
            })
            db.commit()
            db.close()
            
            # Emit completion
            self.workflow_completed.emit({
                "scan_id": self.scan_id,
                "status": "completed" if not self._stop_requested else "cancelled",
                "results": {k: v.dict() for k, v in self.task_results.items()}
            })
            
        except Exception as e:
            self._handle_workflow_error(str(e))
    
    def _execute_workflow(self):
        """Execute workflow with dependency resolution"""
        completed_tasks: Set[str] = set()
        failed_tasks: Set[str] = set()
        total_tasks = len(self.workflow.tasks)
        
        while len(completed_tasks) + len(failed_tasks) < total_tasks:
            if self._stop_requested:
                break
            
            # Find tasks ready to execute
            ready_tasks = self._get_ready_tasks(completed_tasks, failed_tasks)
            
            if not ready_tasks:
                # Check if we're stuck
                if len(completed_tasks) + len(failed_tasks) < total_tasks:
                    # Some tasks can't run due to failed dependencies
                    remaining = [t for t in self.workflow.tasks 
                               if t.task_id not in completed_tasks and t.task_id not in failed_tasks]
                    for task in remaining:
                        self.task_failed.emit(task.task_id, "Dependency failed")
                        failed_tasks.add(task.task_id)
                break
            
            # Sort by priority
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)
            
            # Execute highest priority task
            task = ready_tasks[0]
            success = self._execute_task(task)
            
            if success:
                completed_tasks.add(task.task_id)
            else:
                failed_tasks.add(task.task_id)
            
            # Update progress
            progress = int(((len(completed_tasks) + len(failed_tasks)) / total_tasks) * 100)
            self.progress_updated.emit(progress)
    
    def _get_ready_tasks(self, completed: Set[str], failed: Set[str]) -> List:
        """Get tasks that are ready to execute"""
        ready = []
        
        for task in self.workflow.tasks:
            # Skip if already processed
            if task.task_id in completed or task.task_id in failed:
                continue
            
            # Check if all dependencies are satisfied
            deps_satisfied = True
            for dep_id in task.depends_on:
                if dep_id in failed:
                    # Dependency failed, this task cannot run
                    deps_satisfied = False
                    break
                if dep_id not in completed:
                    deps_satisfied = False
                    break
            
            if deps_satisfied:
                ready.append(task)
        
        return ready
    
    def _execute_task(self, task_def) -> bool:
        """Execute a single task"""
        self.task_started.emit(task_def.task_id, task_def.name)
        
        # Create task record
        db = SessionLocal()
        task_record = Task(
            scan_id=self.scan_id,
            task_name=task_def.name,
            tool=task_def.tool,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(task_record)
        db.commit()
        task_id_db = task_record.id
        db.close()
        
        try:
            # Substitute parameters from previous results
            params = self._substitute_parameters(task_def.parameters)
            
            # Get tool and execute
            tool = self.tool_registry.get_tool(task_def.tool)
            result = tool.execute(params)
            
            # Create task result
            task_result = TaskResult(
                task_id=task_def.task_id,
                status=TaskStatus.COMPLETED if result["success"] else TaskStatus.FAILED,
                output=result.get("data", {}),
                errors=[result.get("error", "")] if not result["success"] else [],
                execution_time=result.get("execution_time", 0),
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.task_results[task_def.task_id] = task_result
            
            # Update task record
            db = SessionLocal()
            task_record = db.query(Task).filter(Task.id == task_id_db).first()
            task_record.status = "completed" if result["success"] else "failed"
            task_record.completed_at = datetime.utcnow()
            task_record.output = json.dumps(result.get("data", {}))
            task_record.errors = result.get("error", "")
            db.commit()
            db.close()
            
            self.task_completed.emit(task_def.task_id, result)
            
            return result["success"]
            
        except Exception as e:
            error_msg = str(e)
            
            # Create failed task result
            task_result = TaskResult(
                task_id=task_def.task_id,
                status=TaskStatus.FAILED,
                output={},
                errors=[error_msg],
                execution_time=0,
                timestamp=datetime.utcnow().isoformat()
            )
            self.task_results[task_def.task_id] = task_result
            
            # Update task record
            db = SessionLocal()
            task_record = db.query(Task).filter(Task.id == task_id_db).first()
            task_record.status = "failed"
            task_record.completed_at = datetime.utcnow()
            task_record.errors = error_msg
            db.commit()
            db.close()
            
            self.task_failed.emit(task_def.task_id, error_msg)
            
            return False
    
    def _substitute_parameters(self, params: Dict) -> Dict:
        """Substitute dynamic parameters from previous task outputs"""
        substituted = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract reference path (e.g., "${recon_subdomains.unique_subdomains}")
                ref_path = value[2:-1]
                parts = ref_path.split(".")
                
                task_id = parts[0]
                if task_id in self.task_results:
                    data = self.task_results[task_id].output
                    
                    # Navigate the path
                    for part in parts[1:]:
                        if isinstance(data, dict) and part in data:
                            data = data[part]
                        else:
                            data = None
                            break
                    
                    substituted[key] = data if data is not None else []
                else:
                    substituted[key] = []
            elif isinstance(value, list):
                # Recursively substitute in lists
                substituted[key] = [
                    self._substitute_parameters({"item": item})["item"]
                    if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively substitute in dicts
                substituted[key] = self._substitute_parameters(value)
            else:
                substituted[key] = value
        
        return substituted
    
    def _handle_workflow_error(self, error: str):
        """Handle workflow-level error"""
        db = SessionLocal()
        scan = db.query(Scan).filter(Scan.id == self.scan_id).first()
        if scan:
            scan.status = "failed"
            scan.completed_at = datetime.utcnow()
            db.commit()
        db.close()
        
        self.workflow_completed.emit({
            "scan_id": self.scan_id,
            "status": "failed",
            "error": error,
            "results": {}
        })
    
    def stop(self):
        """Request workflow stop"""
        self._stop_requested = True