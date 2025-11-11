from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence

from .login_widget import LoginWidget
from .dashboard_widget import DashboardWidget
from .workflow_widget import WorkflowWidget
from .terminal_widget import TerminalWidget
from .report_widget import ReportWidget

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.current_user = None
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Offensive Security Platform")
        self.setMinimumSize(1024, 768)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create pages
        self.login_page = LoginWidget()
        self.dashboard_page = DashboardWidget()
        self.workflow_page = WorkflowWidget()
        self.terminal_page = TerminalWidget()
        self.report_page = ReportWidget()
        
        # Add pages to stack
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.workflow_page)
        self.stacked_widget.addWidget(self.terminal_page)
        self.stacked_widget.addWidget(self.report_page)
        
        # Connect signals
        self.login_page.login_successful.connect(self.on_login_success)
        self.dashboard_page.workflow_selected.connect(self.launch_workflow)
        self.dashboard_page.terminal_requested.connect(self.show_terminal)
        self.dashboard_page.reports_requested.connect(self.show_reports)
        self.dashboard_page.logout_requested.connect(self.logout)
        
        # Show login page
        self.show_login()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Emergency exit: Ctrl+Alt+Q (triple confirmation required)
        from PyQt5.QtWidgets import QShortcut
        
        exit_shortcut = QShortcut(QKeySequence("Ctrl+Alt+Q"), self)
        exit_shortcut.activated.connect(self.emergency_exit)
        
    def emergency_exit(self):
        """Emergency exit with confirmation"""
        reply = QMessageBox.question(
            self,
            'Emergency Exit',
            'Are you sure you want to exit the platform?\n'
            'This will close the application completely.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Second confirmation
            reply2 = QMessageBox.warning(
                self,
                'Confirm Exit',
                'This action cannot be undone.\n'
                'Exit anyway?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply2 == QMessageBox.Yes:
                QApplication.quit()
    
    def show_login(self):
        """Show login page"""
        self.stacked_widget.setCurrentWidget(self.login_page)
        
    def show_dashboard(self):
        """Show dashboard page"""
        self.dashboard_page.load_user_data(self.current_user)
        self.stacked_widget.setCurrentWidget(self.dashboard_page)
        
    def show_terminal(self):
        """Show terminal page"""
        self.stacked_widget.setCurrentWidget(self.terminal_page)
        self.terminal_page.set_return_callback(self.show_dashboard)
        
    def show_reports(self):
        """Show reports page"""
        self.report_page.load_reports(self.current_user)
        self.stacked_widget.setCurrentWidget(self.report_page)
        self.report_page.set_return_callback(self.show_dashboard)
        
    def launch_workflow(self, workflow_id):
        """Launch a workflow"""
        self.workflow_page.start_workflow(workflow_id, self.current_user)
        self.stacked_widget.setCurrentWidget(self.workflow_page)
        self.workflow_page.set_return_callback(self.show_dashboard)
        
    def on_login_success(self, user):
        """Handle successful login"""
        self.current_user = user
        self.show_dashboard()
        
        # Show cursor after login
        QApplication.restoreOverrideCursor()
        
    def logout(self):
        """Logout user"""
        self.current_user = None
        self.login_page.clear_form()
        self.show_login()
        
    def closeEvent(self, event):
        """Handle window close event"""
        # In fullscreen mode, prevent closing
        if self.isFullScreen():
            event.ignore()
            QMessageBox.warning(
                self,
                'Exit Disabled',
                'Use Ctrl+Alt+Q to exit the application.'
            )
        else:
            event.accept()