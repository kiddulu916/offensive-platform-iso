"""
Workflow execution widget
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QScrollArea, QFrame, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

from app.workflows.engine import WorkflowWorker
from app.workflows.prebuilt.web_app_scan import create_web_app_workflow
from app.workflows.prebuilt import WorkflowFactory

class TaskItem(QFrame):
    """Widget representing a single task"""
    
    def __init__(self, task_id: str, task_name: str):
        super().__init__()
        self.task_id = task_id
        self.task_name = task_name
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI"""
        self.setFrameStyle(QFrame.Box)
        self.setMaximumHeight(60)
        
        layout = QHBoxLayout(self)
        
        # Status indicator
        self.status_label = QLabel("⏳")
        self.status_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.status_label)
        
        # Task name
        name_label = QLabel(self.task_name)
        name_label.setFont(QFont("Arial", 11))
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Status text
        self.status_text = QLabel("Pending")
        layout.addWidget(self.status_text)
        
        self.setStyleSheet("""
            TaskItem {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                margin: 2px;
            }
        """)
    
    def set_running(self):
        """Mark task as running"""
        self.status_label.setText("⚙️")
        self.status_text.setText("Running...")
        self.status_text.setStyleSheet("color: #ffaa00;")
        
    def set_completed(self):
        """Mark task as completed"""
        self.status_label.setText("✅")
        self.status_text.setText("Completed")
        self.status_text.setStyleSheet("color: #00ff00;")
        
    def set_failed(self, error: str):
        """Mark task as failed"""
        self.status_label.setText("❌")
        self.status_text.setText("Failed")
        self.status_text.setStyleSheet("color: #ff0000;")

class WorkflowWidget(QWidget):
    """Widget for executing and monitoring workflows"""
    
    def __init__(self):
        super().__init__()
        self.workflow_worker = None
        self.return_callback = None
        self.task_widgets = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Workflow Execution")
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Back button
        self.back_btn = QPushButton("← Back to Dashboard")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(self.back_btn)
        
        layout.addLayout(header_layout)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left side - Task list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        tasks_label = QLabel("Tasks")
        tasks_label.setFont(QFont("Arial", 14, QFont.Bold))
        left_layout.addWidget(tasks_label)
        
        # Scroll area for tasks
        task_scroll = QScrollArea()
        task_scroll.setWidgetResizable(True)
        task_scroll.setMinimumWidth(400)
        
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.addStretch()
        
        task_scroll.setWidget(self.task_container)
        left_layout.addWidget(task_scroll)
        
        # Overall progress
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Overall Progress")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        progress_layout.addWidget(self.progress_bar)
        
        left_layout.addLayout(progress_layout)
        
        content_layout.addWidget(left_panel)
        
        # Right side - Output log
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        output_label = QLabel("Execution Log")
        output_label.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumWidth(500)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        right_layout.addWidget(self.output_text)
        
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout)
        
    def start_workflow(self, workflow_spec: str, user):
        """Start a workflow execution"""
        # Parse workflow spec (format: "workflow_id:target")
        parts = workflow_spec.split(":", 1)
        workflow_id = parts[0]
        target = parts[1] if len(parts) > 1 else ""
        
        try:
            # Use factory to create workflow
            workflow = WorkflowFactory.create_workflow(workflow_id, target)
        
        except ValueError as e:
            self.log_output(f"Error: {str(e)}")
            return
        
        # Create workflow definition
        if workflow_id == "web_app_full":
            workflow = create_web_app_workflow(target)
        else:
            self.log_output(f"Unknown workflow: {workflow_id}")
            return
        
        self.title_label.setText(f"{workflow.name} - {target}")
        
        # Clear previous tasks
        while self.task_layout.count() > 1:
            item = self.task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.task_widgets.clear()
        
        # Create task widgets
        for task in workflow.tasks:
            task_widget = TaskItem(task.task_id, task.name)
            self.task_widgets[task.task_id] = task_widget
            self.task_layout.insertWidget(self.task_layout.count() - 1, task_widget)
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.output_text.clear()
        
        # Create and start worker
        self.workflow_worker = WorkflowWorker(workflow, user.id)
        self.workflow_worker.task_started.connect(self.on_task_started)
        self.workflow_worker.task_completed.connect(self.on_task_completed)
        self.workflow_worker.task_failed.connect(self.on_task_failed)
        self.workflow_worker.workflow_completed.connect(self.on_workflow_completed)
        
        self.log_output(f"Starting workflow: {workflow.name}")
        self.log_output(f"Target: {target}")
        self.log_output("-" * 50)
        
        self.workflow_worker.start()
        
    def on_task_started(self, task_id: str, task_name: str):
        """Handle task started"""
        if task_id in self.task_widgets:
            self.task_widgets[task_id].set_running()
        
        self.log_output(f"\n[STARTED] {task_name}")
        
    def on_task_completed(self, task_id: str, result: dict):
        """Handle task completed"""
        if task_id in self.task_widgets:
            self.task_widgets[task_id].set_completed()
        
        # Update progress
        completed = sum(1 for w in self.task_widgets.values() 
                       if w.status_text.text() in ["Completed", "Failed"])
        progress = int((completed / len(self.task_widgets)) * 100)
        self.progress_bar.setValue(progress)
        
        self.log_output(f"[COMPLETED] {task_id}")
        if result.get("data"):
            import json
            self.log_output(f"Results: {json.dumps(result['data'], indent=2)}")
        
    def on_task_failed(self, task_id: str, error: str):
        """Handle task failed"""
        if task_id in self.task_widgets:
            self.task_widgets[task_id].set_failed(error)
        
        self.log_output(f"[FAILED] {task_id}: {error}")
        
    def on_workflow_completed(self, results: dict):
        """Handle workflow completion"""
        self.log_output("\n" + "=" * 50)
        self.log_output("Workflow completed!")
        self.log_output(f"Scan ID: {results['scan_id']}")
        self.log_output("=" * 50)
        
        # Enable back button
        self.back_btn.setEnabled(True)
        
    def log_output(self, message: str):
        """Add message to output log"""
        self.output_text.append(message)
        self.output_text.moveCursor(QTextCursor.End)
        
    def set_return_callback(self, callback):
        """Set callback for return button"""
        self.return_callback = callback
        
    def on_back_clicked(self):
        """Handle back button click"""
        if self.workflow_worker and self.workflow_worker.isRunning():
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                'Workflow Running',
                'A workflow is currently running. Are you sure you want to go back?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        if self.return_callback:
            self.return_callback()