# Scan Deletion Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement functionality to delete scan history records and all associated files (raw scans, parsed results, reports)

**Architecture:** Add database service layer with cascade deletion, integrate delete button into dashboard UI with confirmation dialog, implement file cleanup logic for scan data directories

**Tech Stack:** SQLAlchemy (ORM), PyQt5 (UI), Python pathlib (file operations)

---

## Task 1: Create Database Service Layer for Scan Deletion

**Files:**
- Create: `app/core/scan_service.py`
- Test: `tests/unit/test_scan_service.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_scan_service.py
import pytest
from app.core.database import SessionLocal, Scan, Task, Subdomain, IP, Port, ASN
from app.core.scan_service import delete_scan
from datetime import datetime


def test_delete_scan_removes_database_records():
    """Test that delete_scan removes scan and all related database records"""
    db = SessionLocal()

    # Create test scan
    scan = Scan(
        user_id=1,
        workflow_name="test_workflow",
        target="example.com",
        status="completed",
        started_at=datetime.utcnow()
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id

    # Create related task
    task = Task(
        scan_id=scan_id,
        task_name="test_task",
        tool="nmap",
        status="completed"
    )
    db.add(task)
    db.commit()

    # Delete scan
    result = delete_scan(scan_id)

    # Verify deletion
    assert result["success"] is True
    assert db.query(Scan).filter(Scan.id == scan_id).first() is None
    assert db.query(Task).filter(Task.scan_id == scan_id).first() is None

    db.close()


def test_delete_scan_with_nonexistent_id():
    """Test that delete_scan handles nonexistent scan ID gracefully"""
    result = delete_scan(999999)

    assert result["success"] is False
    assert "not found" in result["error"].lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_scan_service.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.core.scan_service'"

**Step 3: Write minimal implementation**

```python
# app/core/scan_service.py
"""
Service layer for scan operations including deletion with cascade cleanup
"""
import logging
from typing import Dict, Any
from pathlib import Path
from app.core.database import SessionLocal, Scan, Task, Subdomain, IP, Port, ASN

logger = logging.getLogger(__name__)


def delete_scan(scan_id: int) -> Dict[str, Any]:
    """
    Delete a scan and all associated database records and files.

    Args:
        scan_id: ID of the scan to delete

    Returns:
        Dict with 'success' (bool) and optional 'error' (str) or 'deleted_files' (list)
    """
    db = SessionLocal()

    try:
        # Find the scan
        scan = db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            return {
                "success": False,
                "error": f"Scan with ID {scan_id} not found"
            }

        target = scan.target
        logger.info(f"Deleting scan {scan_id} for target {target}")

        # Delete related records (cascade)
        # SQLAlchemy relationships will handle cascade if configured
        # Otherwise, we delete manually

        # Delete tasks
        db.query(Task).filter(Task.scan_id == scan_id).delete()

        # Delete subdomains (cascade to associations)
        db.query(Subdomain).filter(Subdomain.scan_id == scan_id).delete()

        # Delete IPs
        db.query(IP).filter(IP.scan_id == scan_id).delete()

        # Delete ports
        db.query(Port).filter(Port.scan_id == scan_id).delete()

        # Delete ASNs
        db.query(ASN).filter(ASN.scan_id == scan_id).delete()

        # Delete the scan itself
        db.delete(scan)
        db.commit()

        logger.info(f"Successfully deleted scan {scan_id} from database")

        return {
            "success": True,
            "deleted_files": []
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting scan {scan_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_scan_service.py::test_delete_scan_removes_database_records -v`
Expected: PASS

Run: `pytest tests/unit/test_scan_service.py::test_delete_scan_with_nonexistent_id -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_scan_service.py app/core/scan_service.py
git commit -m "feat: add scan deletion service with database cascade"
```

---

## Task 2: Add File Cleanup to Scan Deletion

**Files:**
- Modify: `app/core/scan_service.py`
- Test: `tests/unit/test_scan_service.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_scan_service.py (add to existing file)
import os
import json
from pathlib import Path


def test_delete_scan_removes_associated_files():
    """Test that delete_scan removes scan result files from filesystem"""
    db = SessionLocal()

    # Create test scan
    scan = Scan(
        user_id=1,
        workflow_name="test_workflow",
        target="testdomain.com",
        status="completed",
        started_at=datetime.utcnow()
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id

    # Create test files that would be generated by scan
    scan_dir = Path("data/scans/testdomain.com")
    scan_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = scan_dir / "raw" / "nmap"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "output.txt").write_text("test raw output")

    parsed_dir = scan_dir / "parsed" / "nmap"
    parsed_dir.mkdir(parents=True, exist_ok=True)
    (parsed_dir / "results.json").write_text(json.dumps({"test": "data"}))

    # Delete scan
    result = delete_scan(scan_id)

    # Verify file deletion
    assert result["success"] is True
    assert not scan_dir.exists()
    assert len(result["deleted_files"]) > 0

    db.close()


def test_delete_scan_handles_missing_files():
    """Test that delete_scan succeeds even if scan files don't exist"""
    db = SessionLocal()

    scan = Scan(
        user_id=1,
        workflow_name="test_workflow",
        target="nonexistent.com",
        status="completed",
        started_at=datetime.utcnow()
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id

    # Don't create any files
    result = delete_scan(scan_id)

    # Should still succeed
    assert result["success"] is True
    assert db.query(Scan).filter(Scan.id == scan_id).first() is None

    db.close()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_scan_service.py::test_delete_scan_removes_associated_files -v`
Expected: FAIL with assertion error (files still exist)

**Step 3: Update implementation with file cleanup**

```python
# app/core/scan_service.py (update delete_scan function)
import shutil

def delete_scan(scan_id: int) -> Dict[str, Any]:
    """
    Delete a scan and all associated database records and files.

    Args:
        scan_id: ID of the scan to delete

    Returns:
        Dict with 'success' (bool) and optional 'error' (str) or 'deleted_files' (list)
    """
    db = SessionLocal()
    deleted_files = []

    try:
        # Find the scan
        scan = db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            return {
                "success": False,
                "error": f"Scan with ID {scan_id} not found"
            }

        target = scan.target
        # Clean target to get directory name
        target_clean = target.replace("http://", "").replace("https://", "")
        target_clean = target_clean.split("/")[0].split(":")[0]

        logger.info(f"Deleting scan {scan_id} for target {target}")

        # Delete database records first
        db.query(Task).filter(Task.scan_id == scan_id).delete()
        db.query(Subdomain).filter(Subdomain.scan_id == scan_id).delete()
        db.query(IP).filter(IP.scan_id == scan_id).delete()
        db.query(Port).filter(Port.scan_id == scan_id).delete()
        db.query(ASN).filter(ASN.scan_id == scan_id).delete()
        db.delete(scan)
        db.commit()

        logger.info(f"Successfully deleted scan {scan_id} from database")

        # Delete associated files
        scan_data_dir = Path("data/scans") / target_clean

        if scan_data_dir.exists():
            try:
                shutil.rmtree(scan_data_dir)
                deleted_files.append(str(scan_data_dir))
                logger.info(f"Deleted scan directory: {scan_data_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete scan directory {scan_data_dir}: {e}")

        # Delete report file if it exists
        if scan.report_path:
            report_path = Path(scan.report_path)
            if report_path.exists():
                try:
                    report_path.unlink()
                    deleted_files.append(str(report_path))
                    logger.info(f"Deleted report file: {report_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete report {report_path}: {e}")

        # Check for tool-specific directories (masscan, nmap, etc.)
        tools_dir = Path("data/scans")
        for tool_dir in ["masscan", "nmap", "nuclei", "subfinder"]:
            tool_path = tools_dir / tool_dir
            if tool_path.exists():
                # Look for files related to this scan_id
                for subdir in ["raw", "parsed"]:
                    scan_subdir = tool_path / subdir
                    if scan_subdir.exists():
                        # Delete files with scan_id in name
                        for file in scan_subdir.glob(f"*{scan_id}*"):
                            try:
                                file.unlink()
                                deleted_files.append(str(file))
                                logger.info(f"Deleted tool file: {file}")
                            except Exception as e:
                                logger.warning(f"Failed to delete {file}: {e}")

        return {
            "success": True,
            "deleted_files": deleted_files
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting scan {scan_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_scan_service.py::test_delete_scan_removes_associated_files -v`
Expected: PASS

Run: `pytest tests/unit/test_scan_service.py::test_delete_scan_handles_missing_files -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/core/scan_service.py tests/unit/test_scan_service.py
git commit -m "feat: add file cleanup to scan deletion service"
```

---

## Task 3: Add Delete Button to Dashboard Scan History

**Files:**
- Modify: `app/gui/dashboard_widget.py:66-125` (ScanHistoryItem class)
- Test: Manual UI testing (no automated UI tests yet)

**Step 1: Add delete signal and button to ScanHistoryItem**

```python
# app/gui/dashboard_widget.py (update ScanHistoryItem class)
class ScanHistoryItem(QFrame):
    """Item widget for scan history"""

    view_clicked = pyqtSignal(int)  # scan_id
    delete_clicked = pyqtSignal(int)  # scan_id  # NEW

    def __init__(self, scan: Scan):
        super().__init__()
        self.scan = scan
        self.setup_ui()

    def setup_ui(self):
        """Setup the item UI"""
        self.setFrameStyle(QFrame.Box)
        self.setMaximumHeight(80)

        layout = QHBoxLayout(self)

        # Status indicator
        status_color = {
            "completed": "#00ff00",
            "running": "#ffaa00",
            "failed": "#ff0000",
            "pending": "#888888"
        }.get(self.scan.status, "#888888")

        status_label = QLabel("●")
        status_label.setStyleSheet(f"color: {status_color}; font-size: 24px;")
        layout.addWidget(status_label)

        # Info
        info_layout = QVBoxLayout()

        name_label = QLabel(f"{self.scan.workflow_name}")
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        info_layout.addWidget(name_label)

        target_label = QLabel(f"Target: {self.scan.target}")
        info_layout.addWidget(target_label)

        time_label = QLabel(f"Started: {self.scan.started_at.strftime('%Y-%m-%d %H:%M')}")
        time_label.setStyleSheet("color: #888;")
        info_layout.addWidget(time_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # View button (only for completed scans)
        if self.scan.status == "completed":
            view_btn = QPushButton("View Report")
            view_btn.clicked.connect(lambda: self.view_clicked.emit(self.scan.id))
            layout.addWidget(view_btn)

        # Delete button (NEW - for all scans)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.scan.id))
        layout.addWidget(delete_btn)

        self.setStyleSheet("""
            ScanHistoryItem {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                margin: 2px;
            }
            QPushButton#deleteButton {
                background-color: #aa0000;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton#deleteButton:hover {
                background-color: #ff0000;
            }
        """)
```

**Step 2: Connect delete signal in DashboardWidget**

```python
# app/gui/dashboard_widget.py (update load_recent_scans method around line 240-264)
    def load_recent_scans(self):
        """Load recent scans from database"""
        # Clear existing items
        while self.history_layout.count() > 1:
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load scans
        db = SessionLocal()
        scans = db.query(Scan).filter(
            Scan.user_id == self.current_user.id
        ).order_by(Scan.started_at.desc()).limit(10).all()
        db.close()

        if not scans:
            no_scans_label = QLabel("No scans yet. Launch a workflow to get started!")
            no_scans_label.setAlignment(Qt.AlignCenter)
            no_scans_label.setStyleSheet("color: #888; padding: 20px;")
            self.history_layout.insertWidget(0, no_scans_label)
        else:
            for scan in scans:
                item = ScanHistoryItem(scan)
                item.view_clicked.connect(self.on_view_report)
                item.delete_clicked.connect(self.on_delete_scan)  # NEW
                self.history_layout.insertWidget(self.history_layout.count() - 1, item)
```

**Step 3: Run application to verify button appears**

Run: `python3 main.py --debug`
Expected: Dashboard shows delete button (red) next to each scan in history

**Step 4: Commit**

```bash
git add app/gui/dashboard_widget.py
git commit -m "feat: add delete button to scan history items"
```

---

## Task 4: Implement Delete Confirmation Dialog

**Files:**
- Modify: `app/gui/dashboard_widget.py` (add on_delete_scan method)
- Test: Manual UI testing

**Step 1: Add on_delete_scan method with confirmation**

```python
# app/gui/dashboard_widget.py (add after on_view_report method, around line 281)
    def on_delete_scan(self, scan_id: int):
        """Handle delete scan button click with confirmation"""
        from app.core.scan_service import delete_scan

        # Get scan details for confirmation message
        db = SessionLocal()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        db.close()

        if not scan:
            QMessageBox.warning(
                self,
                "Error",
                f"Scan {scan_id} not found"
            )
            return

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this scan?\n\n"
            f"Workflow: {scan.workflow_name}\n"
            f"Target: {scan.target}\n"
            f"Started: {scan.started_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"This will permanently delete:\n"
            f"- Scan database record\n"
            f"- All task records\n"
            f"- Raw and parsed scan files\n"
            f"- Generated reports\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No for safety
        )

        if reply == QMessageBox.Yes:
            # Perform deletion
            result = delete_scan(scan_id)

            if result["success"]:
                # Show success message
                deleted_count = len(result.get("deleted_files", []))
                QMessageBox.information(
                    self,
                    "Deletion Complete",
                    f"Successfully deleted scan {scan_id}\n"
                    f"Removed {deleted_count} file(s)/directory(ies)"
                )

                # Refresh scan history
                self.load_recent_scans()
            else:
                # Show error
                QMessageBox.critical(
                    self,
                    "Deletion Failed",
                    f"Failed to delete scan:\n{result.get('error', 'Unknown error')}"
                )
```

**Step 2: Run application to verify confirmation dialog**

Run: `python3 main.py --debug`
Actions:
1. Login to application
2. Navigate to dashboard
3. Click delete button on a scan
4. Verify confirmation dialog appears with scan details
5. Click "No" - verify nothing is deleted
6. Click delete again, click "Yes" - verify scan is deleted and success message appears
7. Verify scan no longer appears in history list

Expected: All verification steps pass

**Step 3: Commit**

```bash
git add app/gui/dashboard_widget.py
git commit -m "feat: implement delete scan with confirmation dialog"
```

---

## Task 5: Add Integration Test for Complete Deletion Flow

**Files:**
- Create: `tests/integration/test_scan_deletion.py`

**Step 1: Write integration test**

```python
# tests/integration/test_scan_deletion.py
import pytest
import json
from pathlib import Path
from datetime import datetime
from app.core.database import SessionLocal, Scan, Task, Subdomain, IP, Port
from app.core.scan_service import delete_scan


def test_complete_scan_deletion_flow():
    """Integration test: create scan with files and database records, then delete everything"""
    db = SessionLocal()

    # Create scan with full database structure
    scan = Scan(
        user_id=1,
        workflow_name="web_app_full",
        target="integration-test.com",
        status="completed",
        started_at=datetime.utcnow(),
        results=json.dumps({"test": "data"})
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id

    # Create tasks
    task1 = Task(
        scan_id=scan_id,
        task_name="subdomain_enum",
        tool="subfinder",
        status="completed",
        output=json.dumps({"subdomains": ["sub1.integration-test.com"]})
    )
    task2 = Task(
        scan_id=scan_id,
        task_name="port_scan",
        tool="nmap",
        status="completed"
    )
    db.add_all([task1, task2])
    db.commit()

    # Create subdomain with relationships
    subdomain = Subdomain(
        scan_id=scan_id,
        name="sub1.integration-test.com",
        source="subfinder"
    )
    db.add(subdomain)
    db.commit()

    ip = IP(
        scan_id=scan_id,
        address="192.168.1.1"
    )
    db.add(ip)
    db.commit()

    port = Port(
        scan_id=scan_id,
        ip_id=ip.id,
        port_number=443,
        service="https"
    )
    db.add(port)
    db.commit()

    # Create file structure
    scan_dir = Path("data/scans/integration-test.com")
    scan_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = scan_dir / "raw" / "subfinder"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "output.txt").write_text("sub1.integration-test.com")

    parsed_dir = scan_dir / "parsed" / "subfinder"
    parsed_dir.mkdir(parents=True, exist_ok=True)
    (parsed_dir / "results.json").write_text(json.dumps({"subdomains": ["sub1.integration-test.com"]}))

    # Verify everything exists
    assert db.query(Scan).filter(Scan.id == scan_id).first() is not None
    assert db.query(Task).filter(Task.scan_id == scan_id).count() == 2
    assert db.query(Subdomain).filter(Subdomain.scan_id == scan_id).count() == 1
    assert db.query(IP).filter(IP.scan_id == scan_id).count() == 1
    assert db.query(Port).filter(Port.scan_id == scan_id).count() == 1
    assert scan_dir.exists()

    # Perform deletion
    result = delete_scan(scan_id)

    # Verify complete cleanup
    assert result["success"] is True
    assert db.query(Scan).filter(Scan.id == scan_id).first() is None
    assert db.query(Task).filter(Task.scan_id == scan_id).count() == 0
    assert db.query(Subdomain).filter(Subdomain.scan_id == scan_id).count() == 0
    assert db.query(IP).filter(IP.scan_id == scan_id).count() == 0
    assert db.query(Port).filter(Port.scan_id == scan_id).count() == 0
    assert not scan_dir.exists()
    assert len(result["deleted_files"]) > 0

    db.close()
```

**Step 2: Run test to verify integration**

Run: `pytest tests/integration/test_scan_deletion.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_scan_deletion.py
git commit -m "test: add integration test for complete scan deletion"
```

---

## Task 6: Add Logging and Error Handling

**Files:**
- Modify: `app/core/scan_service.py`
- Modify: `app/gui/dashboard_widget.py`

**Step 1: Enhance logging in scan_service.py**

```python
# app/core/scan_service.py (update imports and logging)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Update delete_scan function to add detailed logging at each step:
def delete_scan(scan_id: int) -> Dict[str, Any]:
    """
    Delete a scan and all associated database records and files.

    Args:
        scan_id: ID of the scan to delete

    Returns:
        Dict with 'success' (bool) and optional 'error' (str) or 'deleted_files' (list)
    """
    db = SessionLocal()
    deleted_files = []

    try:
        logger.info(f"Starting deletion for scan_id={scan_id}")

        scan = db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            logger.warning(f"Scan {scan_id} not found in database")
            return {
                "success": False,
                "error": f"Scan with ID {scan_id} not found"
            }

        target = scan.target
        target_clean = target.replace("http://", "").replace("https://", "")
        target_clean = target_clean.split("/")[0].split(":")[0]

        logger.info(f"Deleting scan {scan_id}: workflow={scan.workflow_name}, target={target}")

        # Count related records before deletion
        task_count = db.query(Task).filter(Task.scan_id == scan_id).count()
        subdomain_count = db.query(Subdomain).filter(Subdomain.scan_id == scan_id).count()
        ip_count = db.query(IP).filter(IP.scan_id == scan_id).count()
        port_count = db.query(Port).filter(Port.scan_id == scan_id).count()
        asn_count = db.query(ASN).filter(ASN.scan_id == scan_id).count()

        logger.info(f"Deleting related records: {task_count} tasks, {subdomain_count} subdomains, "
                   f"{ip_count} IPs, {port_count} ports, {asn_count} ASNs")

        # Delete related records
        db.query(Task).filter(Task.scan_id == scan_id).delete()
        db.query(Subdomain).filter(Subdomain.scan_id == scan_id).delete()
        db.query(IP).filter(IP.scan_id == scan_id).delete()
        db.query(Port).filter(Port.scan_id == scan_id).delete()
        db.query(ASN).filter(ASN.scan_id == scan_id).delete()
        db.delete(scan)
        db.commit()

        logger.info(f"Successfully deleted scan {scan_id} and all related database records")

        # Delete associated files
        scan_data_dir = Path("data/scans") / target_clean

        if scan_data_dir.exists():
            try:
                shutil.rmtree(scan_data_dir)
                deleted_files.append(str(scan_data_dir))
                logger.info(f"Deleted scan directory: {scan_data_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete scan directory {scan_data_dir}: {e}")
        else:
            logger.debug(f"Scan directory does not exist: {scan_data_dir}")

        # Delete report file if it exists
        if scan.report_path:
            report_path = Path(scan.report_path)
            if report_path.exists():
                try:
                    report_path.unlink()
                    deleted_files.append(str(report_path))
                    logger.info(f"Deleted report file: {report_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete report {report_path}: {e}")

        # Check for tool-specific directories
        tools_dir = Path("data/scans")
        for tool_dir in ["masscan", "nmap", "nuclei", "subfinder", "amass", "httpx", "ffuf", "sqlmap"]:
            tool_path = tools_dir / tool_dir
            if tool_path.exists():
                for subdir in ["raw", "parsed"]:
                    scan_subdir = tool_path / subdir
                    if scan_subdir.exists():
                        for file in scan_subdir.glob(f"*{scan_id}*"):
                            try:
                                file.unlink()
                                deleted_files.append(str(file))
                                logger.info(f"Deleted tool file: {file}")
                            except Exception as e:
                                logger.warning(f"Failed to delete {file}: {e}")

        logger.info(f"Scan deletion complete: {len(deleted_files)} files/directories removed")

        return {
            "success": True,
            "deleted_files": deleted_files
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting scan {scan_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
```

**Step 2: Add error logging to dashboard widget**

```python
# app/gui/dashboard_widget.py (update on_delete_scan method)
    def on_delete_scan(self, scan_id: int):
        """Handle delete scan button click with confirmation"""
        from app.core.scan_service import delete_scan
        from app.core.logging_config import get_logger

        logger = get_logger(__name__)

        # Get scan details for confirmation message
        db = SessionLocal()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        db.close()

        if not scan:
            logger.warning(f"Attempted to delete non-existent scan {scan_id}")
            QMessageBox.warning(
                self,
                "Error",
                f"Scan {scan_id} not found"
            )
            return

        logger.info(f"User requested deletion of scan {scan_id}: {scan.workflow_name} - {scan.target}")

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this scan?\n\n"
            f"Workflow: {scan.workflow_name}\n"
            f"Target: {scan.target}\n"
            f"Started: {scan.started_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"This will permanently delete:\n"
            f"- Scan database record\n"
            f"- All task records\n"
            f"- Raw and parsed scan files\n"
            f"- Generated reports\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.info(f"User confirmed deletion of scan {scan_id}")

            # Perform deletion
            result = delete_scan(scan_id)

            if result["success"]:
                deleted_count = len(result.get("deleted_files", []))
                logger.info(f"Successfully deleted scan {scan_id}, removed {deleted_count} files")

                QMessageBox.information(
                    self,
                    "Deletion Complete",
                    f"Successfully deleted scan {scan_id}\n"
                    f"Removed {deleted_count} file(s)/directory(ies)"
                )

                self.load_recent_scans()
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Failed to delete scan {scan_id}: {error_msg}")

                QMessageBox.critical(
                    self,
                    "Deletion Failed",
                    f"Failed to delete scan:\n{error_msg}"
                )
        else:
            logger.info(f"User cancelled deletion of scan {scan_id}")
```

**Step 3: Test error handling**

Run: `python3 main.py --debug`
Actions:
1. Try to delete a scan - verify logs show detailed information
2. Check `data/logs/platform.log` for deletion logs

Expected: Detailed logging at each step visible in log file

**Step 4: Commit**

```bash
git add app/core/scan_service.py app/gui/dashboard_widget.py
git commit -m "feat: add comprehensive logging and error handling to scan deletion"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add documentation for scan deletion feature**

```markdown
# CLAUDE.md (add new section after "Database Management")

### Scan Deletion

The platform includes functionality to delete scans and clean up associated files.

**Delete a scan programmatically:**
```python
from app.core.scan_service import delete_scan

result = delete_scan(scan_id=123)
if result["success"]:
    print(f"Deleted {len(result['deleted_files'])} files")
else:
    print(f"Error: {result['error']}")
```

**What gets deleted:**
1. Database records:
   - Scan record from `scans` table
   - All related `tasks`
   - All related `subdomains`, `ips`, `ports`, `asns`
2. File system:
   - Scan target directory: `data/scans/{target}/`
   - Tool-specific files: `data/scans/{tool}/raw/*{scan_id}*` and `data/scans/{tool}/parsed/*{scan_id}*`
   - Report file if specified in `scan.report_path`

**UI Access:**
- Click "Delete" button on any scan in dashboard history
- Confirmation dialog prevents accidental deletion
- Success/failure feedback via message box

**Logging:**
All deletion operations are logged to `data/logs/platform.log` with details about:
- Scan being deleted (ID, workflow, target)
- Number of related database records removed
- Files/directories deleted
- Any errors or warnings during cleanup
```

**Step 2: Commit documentation**

```bash
git add CLAUDE.md
git commit -m "docs: add scan deletion feature documentation"
```

---

## Task 8: Manual Testing and Validation

**Files:**
- None (manual testing only)

**Step 1: Full application test**

Test checklist:
1. Start application: `python3 main.py --debug`
2. Login with existing user
3. Verify existing scans show delete button
4. Click delete on a completed scan
5. Verify confirmation dialog shows correct information
6. Click "No" - verify scan still exists
7. Click delete again, click "Yes"
8. Verify success message appears
9. Verify scan removed from history list
10. Check database: `sqlite3 data/platform.db "SELECT COUNT(*) FROM scans;"`
11. Check file system: verify scan directory deleted
12. Check logs: `tail -n 50 data/logs/platform.log`
13. Try deleting a running scan (if available)
14. Try deleting the same scan twice (should show error)
15. Restart application and verify scan still deleted

**Step 2: Document test results**

Create test report in `docs/testing/scan-deletion-manual-test-report.md` documenting results

**Step 3: Final commit**

```bash
git add docs/testing/scan-deletion-manual-test-report.md
git commit -m "test: complete manual testing of scan deletion feature"
```

---

## Summary

This plan implements a complete scan deletion feature with:

1. **Service layer** (`scan_service.py`) handling database and file cleanup
2. **UI integration** (delete button in dashboard with confirmation)
3. **Comprehensive testing** (unit, integration, manual)
4. **Logging** for audit trail and debugging
5. **Documentation** for future developers

**Testing strategy:**
- TDD approach for service layer (write test → fail → implement → pass)
- Manual testing for UI components
- Integration test for complete flow

**Design principles:**
- DRY: Single source of truth in `scan_service.py`
- YAGNI: Only implements requested functionality (delete scan + files)
- Separation of concerns: Service layer handles logic, UI handles presentation
- Safety: Confirmation dialog prevents accidental deletion
- Logging: Full audit trail of deletion operations
