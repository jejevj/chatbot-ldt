"""
Entry point for the application
Run with: uvicorn main_new:app --reload
"""
from app.main import app

__all__ = ['app']
