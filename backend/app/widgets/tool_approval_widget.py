"""
Widget helper for displaying approval requests with approve/reject actions.
"""

from __future__ import annotations

from chatkit.widgets import WidgetRoot, WidgetTemplate

# Load the widget template from file
# Note: The file name has a space, so we need to handle it properly
tool_approval_widget_template = WidgetTemplate.from_file("tool_approval.widget")


def build_approval_widget(question: str) -> WidgetRoot:
    """
    Build an approval widget with approve/reject actions.
    
    This widget displays a card with a title and description, and provides
    approve/reject buttons that trigger request.approve and request.reject actions.
    
    Args:
        question: The title text to display (e.g., "Approve this?")
        
    Returns:
        WidgetRoot: The built widget ready to be streamed to the chat
    """
    payload = {
        "question": question,
    }
    
    return tool_approval_widget_template.build(payload)

