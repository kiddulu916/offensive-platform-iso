"""
Embedded terminal widget
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, QProcess, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

class TerminalWidget(QWidget):
    """Embedded terminal emulator"""
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.return_callback = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("System Terminal")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Warning label
        warning = QLabel("⚠️ Advanced users only - Use with caution")
        warning.setStyleSheet("color: #ffaa00;")
        header_layout.addWidget(warning)
        
        # Back button
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(back_btn)
        
        layout.addLayout(header_layout)
        
        # Terminal display
        self.terminal_display = QTextEdit()
        self.terminal_display.setReadOnly(True)
        self.terminal_display.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.terminal_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        prompt_label = QLabel("$")
        prompt_label.setStyleSheet("color: #00ff00; font-family: 'Courier New'; font-size: 14px;")
        input_layout.addWidget(prompt_label)
        
        self.command_input = QTextEdit()
        self.command_input.setMaximumHeight(40)
        self.command_input.setPlaceholderText("Enter command...")
        self.command_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #444;
                padding: 5px;
            }
        """)
        self.command_input.textChanged.connect(self.on_text_changed)
        input_layout.addWidget(self.command_input)
        
        execute_btn = QPushButton("Execute")
        execute_btn.setMinimumHeight(40)
        execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(execute_btn)
        
        layout.addLayout(input_layout)
        
        # Instructions
        instructions = QLabel(
            "Type commands and press Execute. Press Ctrl+Return to execute. "
            "Common commands: ls, cd, pwd, nmap, subfinder, etc."
        )
        instructions.setStyleSheet("color: #888; font-size: 10px; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Setup process
        self.setup_process()
        
        # Welcome message
        self.append_output("Offensive Platform Terminal")
        self.append_output("=" * 50)
        self.append_output("Type 'help' for available commands")
        self.append_output("")
        
    def setup_process(self):
        """Setup the process for command execution"""
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_process_finished)
        
    def on_text_changed(self):
        """Handle text changed in input"""
        # Check for Ctrl+Return
        text = self.command_input.toPlainText()
        if text.endswith('\n'):
            self.command_input.setPlainText(text.rstrip('\n'))
            self.execute_command()
        
    def execute_command(self):
        """Execute the entered command"""
        command = self.command_input.toPlainText().strip()
        
        if not command:
            return
        
        # Clear input
        self.command_input.clear()
        
        # Show command
        self.append_output(f"$ {command}")
        
        # Handle built-in commands
        if command == "help":
            self.show_help()
            return
        elif command == "clear":
            self.terminal_display.clear()
            return
        
        # Execute external command
        if self.process.state() == QProcess.Running:
            self.append_output("Error: Another command is already running")
            return
        
        # Start process
        self.process.start("bash", ["-c", command])
        
    def on_stdout(self):
        """Handle stdout from process"""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='ignore')
        self.append_output(text)
        
    def on_stderr(self):
        """Handle stderr from process"""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='ignore')
        self.append_output(f"[ERROR] {text}", color="red")
        
    def on_process_finished(self, exit_code, exit_status):
        """Handle process finished"""
        if exit_code != 0:
            self.append_output(f"\nProcess exited with code {exit_code}", color="red")
        self.append_output("")
        
    def append_output(self, text: str, color: str = "#00ff00"):
        """Append text to terminal display"""
        cursor = self.terminal_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        format = cursor.charFormat()
        format.setForeground(Qt.GlobalColor.green if color == "#00ff00" else Qt.GlobalColor.red)
        
        cursor.insertText(text + "\n", format)
        self.terminal_display.setTextCursor(cursor)
        self.terminal_display.ensureCursorVisible()
        
    def show_help(self):
        """Show help information"""
        help_text = """
Available Commands:
-------------------
System:
  ls, cd, pwd       - File system navigation
  clear             - Clear terminal
  help              - Show this help

Security Tools:
  nmap              - Network scanner
  subfinder         - Subdomain enumeration
  httpx             - HTTP probe
  nuclei            - Vulnerability scanner
  sqlmap            - SQL injection tool
  
  For tool-specific help, use: <tool> --help
"""
        self.append_output(help_text)
        
    def set_return_callback(self, callback):
        """Set callback for return button"""
        self.return_callback = callback
        
    def on_back_clicked(self):
        """Handle back button click"""
        if self.return_callback:
            self.return_callback()