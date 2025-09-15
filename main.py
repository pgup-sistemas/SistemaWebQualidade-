#!/usr/bin/env python3
"""
Main application entry point for deployment
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()