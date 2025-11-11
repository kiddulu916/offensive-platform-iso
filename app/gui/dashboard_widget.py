"""
Main dashboard widget
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime

from app.core.database import SessionLocal, Scan

class WorkflowCard(QFrame):
    """Card widget for a workflow option"""
    
    clicked = pyqtSignal(str)  # workflow_id
    
    def __init__(self, workflow_id: str, title: str, description: str):
        super().__init__()
        
        self.workflow_id = workflow_id
        self.setup_ui(title, description)
        
    def setup_ui(self, title: str, description: str):
        """Setup the card UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setMinimumHeight(150)
        self.setMaximumWidth(400)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont("Arial", 14, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Launch button
        launch_btn = QPushButton("Launch")
        launch_btn.setMinimumHeight(35)
        launch_btn.clicked.connect(lambda: self.clicked.emit(self.workflow_id))
        layout.addWidget(launch_btn)
        
        self.setStyleSheet("""
            WorkflowCard {
                background-color: #2b2b2b;
                border: 2px solid #444;
                border-radius: 8px;
                padding: 15px;
            }
            WorkflowCard:hover {
                border-color: #00ff00;
            }
        """)

class ScanHistoryItem(QFrame):
    """Item widget for scan history"""
    
    view_clicked = pyqtSignal(int)  # scan_id
    
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
        
        self.setStyleSheet("""
            ScanHistoryItem {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                margin: 2px;
            }
        """)

class DashboardWidget(QWidget):
    """Main dashboard widget"""
    
    workflow_selected = pyqtSignal(str)  # workflow_id
    terminal_requested = pyqtSignal()
    reports_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("OFFENSIVE SECURITY PLATFORM")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # User info
        self.user_label = QLabel("")
        header_layout.addWidget(self.user_label)
        
        # Terminal button
        terminal_btn = QPushButton("Open Terminal")
        terminal_btn.setMinimumHeight(40)
        terminal_btn.clicked.connect(self.terminal_requested.emit)
        header_layout.addWidget(terminal_btn)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setMinimumHeight(40)
        logout_btn.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(logout_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left side - Workflow cards
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        workflows_label = QLabel("Available Workflows")
        workflows_label.setFont(QFont("Arial", 16, QFont.Bold))
        left_layout.addWidget(workflows_label)
        
        # Scroll area for workflow cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(450)
        
        workflow_container = QWidget()
        workflow_grid = QGridLayout(workflow_container)
        
        # Add workflow cards
        workflows = [
            ("web_app_full", "Full Web Application Scan", "Complete assessment from reconnaissance to exploitation"),
            ("subdomain_enum", "Subdomain Enumeration", "Discover and enumerate all subdomains"),
            ("port_scan", "Port Scanning", "Comprehensive port and service detection"),
            ("vuln_scan", "Vulnerability Scanning", "Automated vulnerability assessment"),
        ]
        
        for idx, (wf_id, title, desc) in enumerate(workflows):
            card = WorkflowCard(wf_id, title, desc)
            card.clicked.connect(self.on_workflow_clicked)
            workflow_grid.addWidget(card, idx // 2, idx % 2)
        
        workflow_grid.setRowStretch(workflow_grid.rowCount(), 1)
        scroll.setWidget(workflow_container)
        left_layout.addWidget(scroll)
        
        content_layout.addWidget(left_panel)
        
        # Right side - Recent scans
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        history_label = QLabel("Recent Scans")
        history_label.setFont(QFont("Arial", 16, QFont.Bold))
        right_layout.addWidget(history_label)
        
        # Scroll area for history
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setMinimumWidth(400)
        
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.addStretch()
        
        self.history_scroll.setWidget(self.history_container)
        right_layout.addWidget(self.history_scroll)
        
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout)
        
    def load_user_data(self, user):
        """Load data for the logged-in user"""
        self.current_user = user
        self.user_label.setText(f"User: {user.username}")
        self.load_recent_scans()
        
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
                self.history_layout.insertWidget(self.history_layout.count() - 1, item)
        
    def on_workflow_clicked(self, workflow_id: str):
        """Handle workflow card click"""
        # Show target input dialog
        from PyQt5.QtWidgets import QInputDialog
        
        target, ok = QInputDialog.getText(
            self,
            "Enter Target",
            f"Enter target URL or domain for {workflow_id}:",
            text="https://example.com"
        )
        
        if ok and target:
            self.workflow_selected.emit(f"{workflow_id}:{target}")
        
    def on_view_report(self, scan_id: int):
        """Handle view report click"""
        # TODO: Implement report viewing
        QMessageBox.information(self, "Report", f"Viewing report for scan {scan_id}")