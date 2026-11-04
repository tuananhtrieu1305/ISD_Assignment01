"""WSGI entry point; implementation is exported from notebook02."""
import os
from project01_llm_v2.transport import create_app
app=create_app(allow_api=os.environ.get('PROJECT01_ENABLE_LIVE_API')=='1')
