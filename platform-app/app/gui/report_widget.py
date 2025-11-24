"""
Report viewing widget
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.core.database import SessionLocal, Scan
import json

class ReportWidget(QWidget):
    """Widget for viewing scan reports"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.return_callback = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Scan Reports")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Back button
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(back_btn)
        
        layout.addLayout(header_layout)
        
        # Splitter for list and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left - Report list
        self.report_list = QListWidget()
        self.report_list.setMinimumWidth(300)
        self.report_list.itemClicked.connect(self.on_report_selected)
        splitter.addWidget(self.report_list)
        
        # Right - Report content
        self.report_content = QTextEdit()
        self.report_content.setReadOnly(True)
        self.report_content.setMinimumWidth(600)
        splitter.addWidget(self.report_content)
        
        layout.addWidget(splitter)
        
    def load_reports(self, user):
        """Load reports for user"""
        self.current_user = user
        self.report_list.clear()

        db = SessionLocal()
        scans = db.query(Scan).filter(
            Scan.user_id == user.id,
            Scan.status == "completed"
        ).order_by(Scan.started_at.desc()).all()
        db.close()

        for scan in scans:
            item = QListWidgetItem(f"{scan.workflow_name} - {scan.target}")
            item.setData(Qt.UserRole, scan.id)
            self.report_list.addItem(item)

        if scans:
            self.report_list.setCurrentRow(0)
            self.on_report_selected(self.report_list.item(0))
        else:
            self.report_content.setPlainText("No reports available")

    def load_scan_report(self, scan_id: int):
        """Load a specific scan report by ID"""
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)

        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()

            if not scan:
                self.report_content.setPlainText(f"Scan {scan_id} not found")
                return

            if not scan.results:
                self.report_content.setPlainText("No results available for this scan")
                return

            try:
                results = json.loads(scan.results)
                report = self.generate_report_text(scan, results)
                self.report_content.setPlainText(report)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse scan results for scan_id={scan_id}: {e}")
                self.report_content.setPlainText("Error: Report data is corrupted")
            except Exception as e:
                logger.error(f"Error generating report for scan_id={scan_id}: {e}")
                self.report_content.setPlainText(f"Error loading report: {str(e)}")
        finally:
            db.close()

    def on_report_selected(self, item):
        """Handle report selection"""
        scan_id = item.data(Qt.UserRole)
        
        db = SessionLocal()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        db.close()
        
        if scan and scan.results:
            try:
                results = json.loads(scan.results)
                report = self.generate_report_text(scan, results)
                self.report_content.setPlainText(report)
            except:
                self.report_content.setPlainText("Error loading report")
        else:
            self.report_content.setPlainText("No results available")
            
    def generate_report_text(self, scan, results):
        """Generate formatted report text"""
        report = []
        report.append("=" * 60)
        report.append(f"SCAN REPORT: {scan.workflow_name}")
        report.append("=" * 60)
        report.append(f"\nTarget: {scan.target}")
        report.append(f"Started: {scan.started_at}")
        report.append(f"Completed: {scan.completed_at}")
        report.append("\n" + "-" * 60)
        
        for task_id, task_result in results.items():
            report.append(f"\nTask: {task_id}")
            report.append(f"Status: {task_result.get('status')}")
            report.append(f"Execution Time: {task_result.get('execution_time', 0):.2f}s")
            
            output = task_result.get('output', {})
            if output:
                report.append("\nResults:")
                report.append(json.dumps(output, indent=2))
            
            errors = task_result.get('errors', [])
            if errors:
                report.append("\nErrors:")
                for error in errors:
                    report.append(f"  - {error}")
            
            report.append("-" * 60)
        
        return "\n".join(report)
        
    def set_return_callback(self, callback):
        """Set callback for return button"""
        self.return_callback = callback
        
    def on_back_clicked(self):
        """Handle back button click"""
        if self.return_callback:
            self.return_callback()