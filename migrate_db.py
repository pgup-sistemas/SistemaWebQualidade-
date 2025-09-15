
"""
Script de migração para adicionar a coluna tipo_documento_id à tabela documents
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    """Adiciona a coluna tipo_documento_id à tabela documents"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='tipo_documento_id'
            """))
            
            if result.fetchone():
                print("Coluna tipo_documento_id já existe!")
                return
            
            # Adicionar a nova coluna
            print("Adicionando coluna tipo_documento_id à tabela documents...")
            db.session.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN tipo_documento_id INTEGER 
                REFERENCES document_types(id)
            """))
            
            db.session.commit()
            print("Migração concluída com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro na migração: {e}")
            print("Tentando criar todas as tabelas...")
            
            # Se der erro, tenta criar todas as tabelas
            db.create_all()
            print("Tabelas criadas/atualizadas!")

if __name__ == '__main__':
    migrate_database()
