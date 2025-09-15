
"""
Script de migração para adicionar a coluna tipo_documento_id à tabela documents
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    """Adiciona as colunas necessárias para tipos dinâmicos"""
    app = create_app()
    
    with app.app_context():
        try:
            # Migração para documentos
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='tipo_documento_id'
            """))
            
            if not result.fetchone():
                print("Adicionando coluna tipo_documento_id à tabela documents...")
                db.session.execute(text("""
                    ALTER TABLE documents 
                    ADD COLUMN tipo_documento_id INTEGER 
                    REFERENCES document_types(id)
                """))
            else:
                print("Coluna tipo_documento_id já existe!")
            
            # Migração para equipamentos
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='equipments' AND column_name='tipo_equipamento_id'
            """))
            
            if not result.fetchone():
                print("Adicionando coluna tipo_equipamento_id à tabela equipments...")
                db.session.execute(text("""
                    ALTER TABLE equipments 
                    ADD COLUMN tipo_equipamento_id INTEGER 
                    REFERENCES equipment_types(id)
                """))
            else:
                print("Coluna tipo_equipamento_id já existe!")
            
            db.session.commit()
            print("Migração concluída com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro na migração: {e}")
            print("Tentando criar todas as tabelas...")
            
            # Se der erro, tenta criar todas as tabelas
            db.create_all()
            print("Tabelas criadas/atualizadas!")
            
            # Criar alguns tipos padrão de equipamentos se não existirem
            try:
                from app.models import EquipmentType, User
                admin = User.query.filter_by(perfil='administrador').first()
                
                if admin and EquipmentType.query.count() == 0:
                    tipos_padrao = [
                        {
                            'codigo': 'MED',
                            'nome': 'Equipamentos de Medição',
                            'descricao': 'Equipamentos para medição e controle dimensional',
                            'cor': '#007bff',
                            'icone': 'bi-speedometer2',
                            'requer_calibracao': True,
                            'frequencia_calibracao_padrao': 12,
                            'requer_manutencao': True,
                            'frequencia_manutencao_padrao': 6
                        },
                        {
                            'codigo': 'TEST',
                            'nome': 'Equipamentos de Teste',
                            'descricao': 'Equipamentos para testes e ensaios',
                            'cor': '#28a745',
                            'icone': 'bi-tools',
                            'requer_calibracao': True,
                            'frequencia_calibracao_padrao': 6,
                            'requer_manutencao': True,
                            'frequencia_manutencao_padrao': 3
                        },
                        {
                            'codigo': 'PROD',
                            'nome': 'Equipamentos de Produção',
                            'descricao': 'Equipamentos utilizados na produção',
                            'cor': '#dc3545',
                            'icone': 'bi-gear',
                            'requer_calibracao': False,
                            'requer_manutencao': True,
                            'frequencia_manutencao_padrao': 12
                        },
                        {
                            'codigo': 'SEG',
                            'nome': 'Equipamentos de Segurança',
                            'descricao': 'Equipamentos de proteção e segurança',
                            'cor': '#ffc107',
                            'icone': 'bi-shield-check',
                            'requer_calibracao': True,
                            'frequencia_calibracao_padrao': 12,
                            'requer_manutencao': True,
                            'frequencia_manutencao_padrao': 6
                        }
                    ]
                    
                    for tipo_data in tipos_padrao:
                        tipo = EquipmentType(
                            codigo=tipo_data['codigo'],
                            nome=tipo_data['nome'],
                            descricao=tipo_data['descricao'],
                            cor=tipo_data['cor'],
                            icone=tipo_data['icone'],
                            requer_calibracao=tipo_data['requer_calibracao'],
                            frequencia_calibracao_padrao=tipo_data.get('frequencia_calibracao_padrao'),
                            requer_manutencao=tipo_data['requer_manutencao'],
                            frequencia_manutencao_padrao=tipo_data.get('frequencia_manutencao_padrao'),
                            criado_por_id=admin.id
                        )
                        db.session.add(tipo)
                    
                    db.session.commit()
                    print("Tipos padrão de equipamentos criados!")
            except Exception as e:
                print(f"Erro ao criar tipos padrão: {e}")

if __name__ == '__main__':
    migrate_database()
