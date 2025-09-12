#!/usr/bin/env python3
"""
Arquivo principal para executar a aplicação Alpha Gestão Documental
"""
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
    app.run(host='0.0.0.0', port=5000, debug=True)