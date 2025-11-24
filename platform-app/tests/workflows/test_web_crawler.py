import pytest
from app.workflows.processors.web_crawler import WebCrawlerProcessor
from app.workflows.schemas import WorkflowTask, TaskType

def test_web_crawler_parse_html():
    """Test HTML parsing for input fields"""
    processor = WebCrawlerProcessor()

    html_content = """
    <html>
    <body>
        <form action="/login" method="post">
            <input type="text" name="username" />
            <input type="password" name="password" />
            <input type="submit" value="Login" />
        </form>
        <form action="/search">
            <input type="text" name="q" />
        </form>
    </body>
    </html>
    """

    forms = processor._parse_forms_from_html(html_content, "http://example.com/page")

    assert len(forms) == 2
    assert forms[0]["action"] == "http://example.com/login"
    assert forms[0]["method"] == "post"
    assert len(forms[0]["inputs"]) == 3

def test_web_crawler_find_text_inputs():
    """Test filtering forms with text inputs"""
    processor = WebCrawlerProcessor()

    forms = [
        {
            "action": "/login",
            "inputs": [
                {"type": "text", "name": "username"},
                {"type": "password", "name": "password"}
            ]
        },
        {
            "action": "/submit",
            "inputs": [
                {"type": "submit", "value": "Go"}
            ]
        }
    ]

    text_input_forms = processor._filter_text_input_forms(forms)
    assert len(text_input_forms) == 1
    assert text_input_forms[0]["action"] == "/login"
