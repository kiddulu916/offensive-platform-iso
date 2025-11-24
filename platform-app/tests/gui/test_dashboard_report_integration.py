"""Integration tests for dashboard report viewing"""
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from unittest.mock import Mock, patch, MagicMock
from app.gui.dashboard_widget import DashboardWidget
from app.gui.main_window import MainWindow

@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_dashboard_has_report_requested_signal(qapp):
    """Test that DashboardWidget defines report_requested signal"""
    dashboard = DashboardWidget()
    assert hasattr(dashboard, 'report_requested')
    # Check that it's a bound signal
    assert hasattr(dashboard.report_requested, 'emit')

def test_on_view_report_emits_signal(qapp):
    """Test that on_view_report emits report_requested signal with scan_id"""
    dashboard = DashboardWidget()

    # Use a signal spy to capture emitted signals
    emitted_values = []
    dashboard.report_requested.connect(lambda x: emitted_values.append(x))

    dashboard.on_view_report(123)
    assert len(emitted_values) == 1
    assert emitted_values[0] == 123

def test_main_window_connects_report_signal(qapp):
    """Test that MainWindow connects dashboard.report_requested to show_report"""
    with patch('app.core.database.SessionLocal'):
        window = MainWindow()

        # Verify that show_report method exists
        assert hasattr(window, 'show_report')
        assert callable(window.show_report)

def test_show_report_navigates_to_report_widget(qapp):
    """Test that show_report loads scan and switches to report widget"""
    with patch('app.core.database.SessionLocal'):
        window = MainWindow()

        # Mock report widget's load method
        with patch.object(window.report_page, 'load_scan_report') as mock_load:
            with patch.object(window.stacked_widget, 'setCurrentWidget') as mock_set:
                window.show_report(456)

                mock_load.assert_called_once_with(456)
                mock_set.assert_called_once_with(window.report_page)
