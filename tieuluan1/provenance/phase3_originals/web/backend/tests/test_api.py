"""Compatibility smoke tests for the public Flask application object."""

from backend.app import API_VERSION, app


def test_wsgi_application_is_importable():
    assert app.name == "backend.app"
    assert API_VERSION == "2.0.0"


def test_wsgi_application_has_render_health_route():
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/health" in rules
    assert "/api/predict/<use_case>" in rules
