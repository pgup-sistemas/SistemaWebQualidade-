#!/usr/bin/env python3
"""
Arquivo principal para executar a aplicação Alpha Gestão Documental
"""
import os
from app import create_app, db
from app.models import User, Document, DocumentVersion, ApprovalFlow

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Document': Document, 
        'DocumentVersion': DocumentVersion,
        'ApprovalFlow': ApprovalFlow
    }

if __name__ == '__main__':
    # Get environment variables for production safety
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes', 'on']
    
    # Force debug=False in production
    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENV') == 'production':
        debug_mode = False
    
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)