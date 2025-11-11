from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

from app.core.auth import AuthManager

class LoginWidget(QWidget):
    """Login and registration widget"""
    
    login_successful = pyqtSignal(object)  # Emits user object
    
    def __init__(self):
        super().__init__()
        
        self.auth_manager = AuthManager()
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Logo/Title
        title = QLabel("OFFENSIVE SECURITY PLATFORM")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 24, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addSpacing(30)
        
        # Login form container
        form_container = QFrame()
        form_container.setMaximumWidth(400)
        form_container.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        
        # Username field
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(40)
        
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addSpacing(10)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self.handle_login)
        
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(45)
        self.login_button.clicked.connect(self.handle_login)
        
        self.register_button = QPushButton("Register")
        self.register_button.setMinimumHeight(45)
        self.register_button.clicked.connect(self.handle_register)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        
        form_layout.addLayout(button_layout)
        
        layout.addWidget(form_container, alignment=Qt.AlignCenter)
        
        # First boot message
        if self.auth_manager.is_first_boot():
            layout.addSpacing(20)
            first_boot_label = QLabel("First boot detected. Please create an account.")
            first_boot_label.setAlignment(Qt.AlignCenter)
            first_boot_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
            layout.addWidget(first_boot_label)
        
    def handle_login(self):
        """Handle login attempt"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        
        user = self.auth_manager.authenticate(username, password)
        
        if user:
            self.login_successful.emit(user)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def handle_register(self):
        """Handle registration"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        
        if len(password) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters")
            return
        
        success, message = self.auth_manager.register(username, password)
        
        if success:
            QMessageBox.information(self, "Success", "Account created successfully! You can now login.")
            self.password_input.clear()
            self.password_input.setFocus()
        else:
            QMessageBox.warning(self, "Registration Failed", message)
    
    def clear_form(self):
        """Clear login form"""
        self.username_input.clear()
        self.password_input.clear()