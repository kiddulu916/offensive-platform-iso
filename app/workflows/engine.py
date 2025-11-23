"""
Workflow execution engine with dependency resolution and parallel execution
"""
from typing import Dict, List, Set, Any
from PyQt5.QtCore import QThread, pyqtSignal
import json
from datetime import datetime
import time
import os
from pathlib import Path

from app.workflows.schemas import WorkflowDefinition, TaskResult, TaskStatus, TaskType
from app.tools.registry import ToolRegistry
from app.core.database import SessionLocal, Scan, Task
from app.core.logging_config import get_workflow_logger

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
        self.logger = get_workflow_logger()  # Will be updated with scan_id once created
        
    def run(self):
        """Execute the workflow"""
        try:
            self.logger.info(f"Initializing workflow: {self.workflow.name}")
            self.logger.info(f"Target: {self.workflow.target}")
            self.logger.info(f"Total tasks: {len(self.workflow.tasks)}")

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

            # Update logger with scan_id
            self.logger = get_workflow_logger(scan_id=self.scan_id)
            self.logger.info(f"Scan record created: scan_id={self.scan_id}")

            # Execute workflow
            workflow_start_time = time.time()
            self.logger.info("Starting workflow execution")
            self._execute_workflow()
            workflow_duration = time.time() - workflow_start_time

            # Mark as completed
            final_status = "completed" if not self._stop_requested else "cancelled"
            self.logger.info(f"Workflow execution {final_status} in {workflow_duration:.2f}s")

            db = SessionLocal()
            scan = db.query(Scan).filter(Scan.id == self.scan_id).first()
            scan.status = final_status
            scan.completed_at = datetime.utcnow()
            scan.results = json.dumps({
                task_id: result.dict()
                for task_id, result in self.task_results.items()
            })
            db.commit()
            db.close()

            # Log final summary
            completed_count = sum(1 for r in self.task_results.values() if r.status == TaskStatus.COMPLETED)
            failed_count = sum(1 for r in self.task_results.values() if r.status == TaskStatus.FAILED)
            self.logger.info(f"Workflow summary: {completed_count} completed, {failed_count} failed")

            # Emit completion
            self.workflow_completed.emit({
                "scan_id": self.scan_id,
                "status": final_status,
                "results": {k: v.dict() for k, v in self.task_results.items()}
            })

        except Exception as e:
            self.logger.exception(f"Workflow execution failed with exception: {e}")
            self._handle_workflow_error(str(e))
    
    def _execute_workflow(self):
        """Execute workflow with dependency resolution"""
        completed_tasks: Set[str] = set()
        failed_tasks: Set[str] = set()
        total_tasks = len(self.workflow.tasks)

        self.logger.debug(f"Entering workflow execution loop (total_tasks={total_tasks})")

        while len(completed_tasks) + len(failed_tasks) < total_tasks:
            if self._stop_requested:
                self.logger.warning("Stop requested, terminating workflow execution")
                break

            # Find tasks ready to execute
            ready_tasks = self._get_ready_tasks(completed_tasks, failed_tasks)
            self.logger.debug(f"Dependency check: {len(ready_tasks)} tasks ready to execute")

            if not ready_tasks:
                # Check if we're stuck
                if len(completed_tasks) + len(failed_tasks) < total_tasks:
                    # Some tasks can't run due to failed dependencies
                    remaining = [t for t in self.workflow.tasks
                               if t.task_id not in completed_tasks and t.task_id not in failed_tasks]
                    self.logger.error(f"Workflow blocked: {len(remaining)} tasks cannot run due to failed dependencies")
                    for task in remaining:
                        self.logger.warning(f"Skipping task {task.task_id} ({task.name}) - dependencies failed")
                        self.task_failed.emit(task.task_id, "Dependency failed")
                        failed_tasks.add(task.task_id)
                break

            # Sort by priority
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)
            task = ready_tasks[0]
            self.logger.info(f"Selected task for execution: {task.task_id} ({task.name}) - priority {task.priority}")

            if len(ready_tasks) > 1:
                self.logger.debug(f"Other ready tasks (lower priority): {[t.task_id for t in ready_tasks[1:]]}")

            # Execute highest priority task
            success = self._execute_task(task)

            if success:
                completed_tasks.add(task.task_id)
                self.logger.info(f"Task {task.task_id} completed successfully")
            else:
                failed_tasks.add(task.task_id)
                self.logger.error(f"Task {task.task_id} failed")

            # Update progress
            progress = int(((len(completed_tasks) + len(failed_tasks)) / total_tasks) * 100)
            self.logger.debug(f"Progress: {progress}% ({len(completed_tasks)} completed, {len(failed_tasks)} failed)")
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
        """Execute a single task (tool or merge)"""
        # Check task type and delegate
        if task_def.task_type == TaskType.MERGE:
            return self._execute_merge_task(task_def)
        else:
            return self._execute_tool_task(task_def)

    def _execute_tool_task(self, task_def) -> bool:
        """Execute a tool task"""
        # Create task-specific logger
        task_logger = get_workflow_logger(
            scan_id=self.scan_id,
            task_id=task_def.task_id,
            tool=task_def.tool
        )

        task_logger.info(f"Starting task: {task_def.name}")
        task_logger.debug(f"Task dependencies: {task_def.depends_on}")
        task_logger.debug(f"Raw parameters: {task_def.parameters}")

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
            task_logger.debug(f"Substituted parameters: {params}")

            # Get tool and execute
            tool = self.tool_registry.get_tool(task_def.tool)
            task_logger.info(f"Executing tool: {task_def.tool}")

            result = tool.execute(params)

            task_logger.info(f"Tool execution completed - success: {result['success']}, "
                           f"duration: {result.get('execution_time', 0):.2f}s")

            if not result["success"]:
                task_logger.error(f"Tool execution failed: {result.get('error', 'Unknown error')}")

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
            task_logger.exception(f"Task execution failed with exception: {error_msg}")

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

    def _execute_merge_task(self, task_def) -> bool:
        """Execute a merge task to combine and deduplicate results"""
        task_logger = get_workflow_logger(
            scan_id=self.scan_id,
            task_id=task_def.task_id,
            tool="merge"
        )

        task_logger.info(f"Starting merge task: {task_def.name}")
        task_logger.debug(f"Merge sources: {task_def.merge_sources}")
        task_logger.debug(f"Merge field: {task_def.merge_field}")
        task_logger.debug(f"Dedupe key: {task_def.dedupe_key}")
        task_logger.debug(f"Merge strategy: {task_def.merge_strategy}")

        self.task_started.emit(task_def.task_id, task_def.name)

        # Create task record
        db = SessionLocal()
        task_record = Task(
            scan_id=self.scan_id,
            task_name=task_def.name,
            tool="merge",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(task_record)
        db.commit()
        task_id_db = task_record.id
        db.close()

        try:
            start_time = time.time()

            # Collect results from source tasks
            source_results = []
            for source_id in task_def.merge_sources:
                if source_id not in self.task_results:
                    raise ValueError(f"Source task '{source_id}' not found in results")

                source_task_result = self.task_results[source_id]
                if source_task_result.status != TaskStatus.COMPLETED:
                    raise ValueError(f"Source task '{source_id}' did not complete successfully")

                # Extract the merge field
                if task_def.merge_field:
                    field_data = source_task_result.output.get(task_def.merge_field, [])
                else:
                    field_data = source_task_result.output

                source_results.append({
                    "task_id": source_id,
                    "data": field_data
                })

                task_logger.debug(f"Collected {len(field_data) if isinstance(field_data, list) else 1} items from {source_id}")

            # Perform merge based on strategy
            merged_data = self._merge_data(
                source_results,
                task_def.dedupe_key,
                task_def.merge_strategy,
                task_logger
            )

            task_logger.info(f"Merged {len(merged_data)} unique items")

            # Get domain from workflow target
            domain = self._extract_domain(self.workflow.target)

            # Create output directory structure
            scan_dir = self._create_scan_directory(domain, task_logger)

            # Save merged results to files
            output_files = self._save_merged_results(
                merged_data,
                scan_dir,
                task_def.task_id,
                task_logger
            )

            execution_time = time.time() - start_time

            # Create task result
            task_result = TaskResult(
                task_id=task_def.task_id,
                status=TaskStatus.COMPLETED,
                output={
                    "merged_data": merged_data,
                    "output_files": output_files,
                    "item_count": len(merged_data)
                },
                execution_time=execution_time,
                timestamp=datetime.utcnow().isoformat()
            )

            self.task_results[task_def.task_id] = task_result

            # Update task record
            db = SessionLocal()
            task_record = db.query(Task).filter(Task.id == task_id_db).first()
            task_record.status = "completed"
            task_record.completed_at = datetime.utcnow()
            task_record.output = json.dumps(task_result.output)
            db.commit()
            db.close()

            task_logger.info(f"Merge task completed successfully in {execution_time:.2f}s")
            self.task_completed.emit(task_def.task_id, {"success": True, "data": task_result.output})

            return True

        except Exception as e:
            error_msg = str(e)
            task_logger.exception(f"Merge task execution failed: {error_msg}")

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

    def _merge_data(self, source_results: List[Dict], dedupe_key: str, strategy: str, logger) -> List[Dict]:
        """Merge and deduplicate data from multiple sources"""
        merged = {}

        for source in source_results:
            data = source["data"]

            if not isinstance(data, list):
                logger.warning(f"Source {source['task_id']} data is not a list, skipping")
                continue

            for item in data:
                if not isinstance(item, dict):
                    logger.debug(f"Skipping non-dict item: {item}")
                    continue

                key = item.get(dedupe_key)
                if not key:
                    logger.debug(f"Item missing dedupe key '{dedupe_key}', skipping: {item}")
                    continue

                if strategy == "combine":
                    # Merge IPs and other fields
                    if key in merged:
                        # Combine IPs
                        if "ips" in item and "ips" in merged[key]:
                            existing_ips = set(merged[key]["ips"]) if isinstance(merged[key]["ips"], list) else {merged[key]["ips"]}
                            new_ips = set(item["ips"]) if isinstance(item["ips"], list) else {item["ips"]}
                            merged[key]["ips"] = list(existing_ips | new_ips)

                        # Combine ASNs
                        if "asns" in item and "asns" in merged[key]:
                            existing_asns = set(merged[key]["asns"]) if isinstance(merged[key]["asns"], list) else {merged[key]["asns"]}
                            new_asns = set(item["asns"]) if isinstance(item["asns"], list) else {item["asns"]}
                            merged[key]["asns"] = list(existing_asns | new_asns)

                        # Update other fields if not present
                        for field_key, field_value in item.items():
                            if field_key not in merged[key] and field_key != dedupe_key:
                                merged[key][field_key] = field_value
                    else:
                        merged[key] = item.copy()

                elif strategy == "replace":
                    # Last source wins
                    merged[key] = item.copy()

                elif strategy == "append":
                    # Keep all entries (append unique ID to key)
                    unique_key = f"{key}_{source['task_id']}"
                    merged[unique_key] = item.copy()

        logger.debug(f"Merge complete: {len(merged)} unique items")
        return list(merged.values())

    def _extract_domain(self, target: str) -> str:
        """Extract clean domain name from target"""
        # Remove protocol
        domain = target.replace("http://", "").replace("https://", "")
        # Remove path
        domain = domain.split("/")[0]
        # Remove port
        domain = domain.split(":")[0]
        return domain

    def _create_scan_directory(self, domain: str, logger) -> Path:
        """Create directory structure for scan results"""
        base_dir = Path("data/scans") / domain
        subdirs = ["raw", "parsed", "lists", "final"]

        for subdir in subdirs:
            dir_path = base_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

        return base_dir

    def _save_merged_results(self, merged_data: List[Dict], scan_dir: Path, task_id: str, logger) -> Dict[str, str]:
        """Save merged results to various file formats"""
        output_files = {}

        try:
            # Save combined JSON to final directory
            combined_json_path = scan_dir / "final" / "subdomains.json"
            with open(combined_json_path, 'w') as f:
                json.dump(merged_data, f, indent=2)
            output_files["combined_json"] = str(combined_json_path)
            logger.info(f"Saved combined JSON: {combined_json_path}")

            # Extract and save plain text lists
            subdomains = []
            ips = set()
            asns = set()

            for item in merged_data:
                if "name" in item:
                    subdomains.append(item["name"])

                if "ips" in item:
                    item_ips = item["ips"] if isinstance(item["ips"], list) else [item["ips"]]
                    ips.update(item_ips)

                if "asns" in item:
                    item_asns = item["asns"] if isinstance(item["asns"], list) else [item["asns"]]
                    asns.update(item_asns)

            # Save subdomains list
            if subdomains:
                subdomains_path = scan_dir / "lists" / "subdomains.txt"
                with open(subdomains_path, 'w') as f:
                    f.write("\n".join(sorted(subdomains)))
                output_files["subdomains_list"] = str(subdomains_path)
                logger.info(f"Saved {len(subdomains)} subdomains to: {subdomains_path}")

            # Save IPs list
            if ips:
                ips_path = scan_dir / "lists" / "ips.txt"
                with open(ips_path, 'w') as f:
                    f.write("\n".join(sorted(ips)))
                output_files["ips_list"] = str(ips_path)
                logger.info(f"Saved {len(ips)} IPs to: {ips_path}")

            # Save ASNs list
            if asns:
                asns_path = scan_dir / "lists" / "asns.txt"
                with open(asns_path, 'w') as f:
                    f.write("\n".join(sorted(asns)))
                output_files["asns_list"] = str(asns_path)
                logger.info(f"Saved {len(asns)} ASNs to: {asns_path}")

            return output_files

        except Exception as e:
            logger.error(f"Error saving merged results: {e}")
            raise

    def _substitute_parameters(self, params: Dict) -> Dict:
        """Substitute dynamic parameters from previous task outputs"""
        substituted = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract reference path (e.g., "${recon_subdomains.unique_subdomains}")
                ref_path = value[2:-1]
                parts = ref_path.split(".")

                task_id = parts[0]
                self.logger.debug(f"Parameter substitution: {key} -> {ref_path}")

                if task_id in self.task_results:
                    data = self.task_results[task_id].output

                    # Navigate the path
                    for part in parts[1:]:
                        if isinstance(data, dict) and part in data:
                            data = data[part]
                        else:
                            self.logger.warning(f"Parameter substitution failed: path '{ref_path}' not found in task {task_id} output")
                            data = None
                            break

                    substituted[key] = data if data is not None else []
                    if data is None:
                        self.logger.debug(f"Substituted {key} with empty list (path not found)")
                    else:
                        self.logger.debug(f"Substituted {key} with value from {ref_path}")
                else:
                    self.logger.warning(f"Parameter substitution failed: task {task_id} not found in results")
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