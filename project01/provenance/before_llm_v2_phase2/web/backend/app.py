"""WSGI entry point; implementation is exported from notebook02."""
from project01_core.transport import create_app
app=create_app()
