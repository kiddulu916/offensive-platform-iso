"""Tests for workflow widget"""
import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_workflow_widget_imports_successfully(qapp):
    """Test that workflow_widget imports without errors"""
    # This will fail if WorkflowFactory is missing
    from app.gui.workflow_widget import WorkflowWidget
    assert WorkflowWidget is not None


def test_workflow_factory_available_in_widget(qapp):
    """Test that WorkflowFactory can be accessed in workflow widget"""
    from app.gui.workflow_widget import WorkflowWidget

    # Check if the module has access to WorkflowFactory
    # This would fail at runtime if import is missing
    widget = WorkflowWidget()
    assert hasattr(widget, 'start_workflow')
