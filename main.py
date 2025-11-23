#!/usr/bin/env python3
"""
Offensive Security Platform
Main application entry point
"""

import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, qInstallMessageHandler, QtMsgType
from PyQt5.QtGui import QIcon

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui.main_window import MainWindow
from app.core.database import init_database
from app.core.logging_config import LoggingConfig


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler to catch all uncaught exceptions and log them
    This ensures exceptions that would normally only print to console are logged
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow KeyboardInterrupt to exit normally
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger("uncaught_exception")
    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    logger.critical(f"Exception type: {exc_type.__name__}")
    logger.critical(f"Exception value: {exc_value}")
    logger.critical("Traceback:\n" + "".join(traceback.format_tb(exc_traceback)))


def qt_message_handler(msg_type, context, message):
    """
    Qt message handler to capture Qt warnings and errors in logs
    """
    logger = logging.getLogger("qt")

    if msg_type == QtMsgType.QtDebugMsg:
        logger.debug(f"Qt: {message}")
    elif msg_type == QtMsgType.QtInfoMsg:
        logger.info(f"Qt: {message}")
    elif msg_type == QtMsgType.QtWarningMsg:
        logger.warning(f"Qt: {message}")
    elif msg_type == QtMsgType.QtCriticalMsg:
        logger.error(f"Qt Critical: {message}")
    elif msg_type == QtMsgType.QtFatalMsg:
        logger.critical(f"Qt Fatal: {message}")
        # Also log to stderr as this is fatal
        print(f"Qt Fatal Error: {message}", file=sys.stderr)

def main():
    # Initialize logging FIRST
    log_level = logging.DEBUG if '--debug' in sys.argv else logging.INFO
    LoggingConfig.setup_logging(level=log_level)
    logger = logging.getLogger(__name__)

    # Install global exception handler to catch uncaught exceptions
    sys.excepthook = global_exception_handler
    logger.info("Global exception handler installed")

    # Install Qt message handler to capture Qt warnings/errors
    qInstallMessageHandler(qt_message_handler)
    logger.info("Qt message handler installed")

    try:
        logger.info("="*60)
        logger.info("Starting Offensive Security Platform")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Arguments: {sys.argv}")
        logger.info("="*60)

        # Initialize database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully")

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Offensive Security Platform")
        app.setOrganizationName("Offensive Platform")

        # Set application style
        app.setStyle('Fusion')

        # Load dark theme
        logger.info("Loading dark theme stylesheet...")
        with open('resources/styles/dark.qss', 'r') as f:
            app.setStyleSheet(f.read())
        logger.info("Stylesheet loaded successfully")

        # Create main window
        logger.info("Creating main window...")
        window = MainWindow()
        logger.info("Main window created successfully")

        # Check for fullscreen flag
        if '--fullscreen' in sys.argv:
            logger.info("Starting in fullscreen mode")
            window.showFullScreen()
            # Hide cursor initially
            app.setOverrideCursor(Qt.BlankCursor)
        else:
            logger.info("Starting in windowed mode")
            window.showMaximized()

        # Disable closing with Alt+F4 in fullscreen mode
        if '--fullscreen' in sys.argv:
            window.setWindowFlags(
                Qt.Window |
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint
            )

        logger.info("Application window created, entering main event loop")
        exit_code = app.exec_()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        logger.exception(f"Fatal error in main(): {e}")
        logger.critical("Application crashed, see traceback above")
        sys.exit(1)

if __name__ == '__main__':
    main()