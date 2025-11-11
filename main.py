#!/usr/bin/env python3
"""
Offensive Security Platform
Main application entry point
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui.main_window import MainWindow
from app.core.database import init_database

def main():
    # Initialize database
    init_database()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Offensive Security Platform")
    app.setOrganizationName("Offensive Platform")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Load dark theme
    with open('resources/styles/dark.qss', 'r') as f:
        app.setStyleSheet(f.read())
    
    # Create main window
    window = MainWindow()
    
    # Check for fullscreen flag
    if '--fullscreen' in sys.argv:
        window.showFullScreen()
        # Hide cursor initially
        app.setOverrideCursor(Qt.BlankCursor)
    else:
        window.showMaximized()
    
    # Disable closing with Alt+F4 in fullscreen mode
    if '--fullscreen' in sys.argv:
        window.setWindowFlags(
            Qt.Window | 
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()