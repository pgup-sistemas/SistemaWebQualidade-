
#!/usr/bin/env python3
"""
Script completo para migrar banco de dados com grupos/setores
"""
from app import create_app, db
from app.models import Group, User, DocumentType
from sqlalchemy import text
import os

def migrate_database():
    """Migração completa do banco de dados"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Iniciando migração do banco de dados...")
            
            # 1. Criar todas as tabelas
            db.create_all()
            print("✓ Tabelas criadas/verificadas")
            
            # 2. Verificar se precisa adicionar colunas na tabela users
            try:
                # Tentar consultar a coluna grupo_id
                result = db.session.execute(text("SELECT grupo_id FROM users LIMIT 1"))
                print("✓ Coluna grupo_id já existe na tabela users")
            except Exception as e:
                if "does not exist" in str(e) or "no such column" in str(e):
                    print("Adicionando colunas na tabela users...")
                    
                    # Detectar tipo de banco
                    database_url = os.environ.get('DATABASE_URL', '')
                    is_postgres = database_url.startswith('postgresql')
                    
                    if is_postgres:
                        # PostgreSQL
                        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS grupo_id INTEGER"))
                        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS cargo VARCHAR(100)"))
                        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS receber_notificacoes BOOLEAN DEFAULT TRUE"))
                        # Adicionar foreign key constraint se não existir
                        try:
                            db.session.execute(text("ALTER TABLE users ADD CONSTRAINT fk_users_grupo_id FOREIGN KEY (grupo_id) REFERENCES groups(id)"))
                        except:
                            pass  # Constraint já existe
                    else:
                        # SQLite
                        db.session.execute(text("ALTER TABLE users ADD COLUMN grupo_id INTEGER"))
                        db.session.execute(text("ALTER TABLE users ADD COLUMN cargo VARCHAR(100)"))
                        db.session.execute(text("ALTER TABLE users ADD COLUMN receber_notificacoes BOOLEAN DEFAULT 1"))
                    
                    db.session.commit()
                    print("✓ Colunas adicionadas na tabela users")
                else:
                    raise e
            
            # 3. Verificar se precisa adicionar colunas na tabela documents
            try:
                result = db.session.execute(text("SELECT tipo_documento_id FROM documents LIMIT 1"))
                print("✓ Coluna tipo_documento_id já existe na tabela documents")
            except Exception as e:
                if "does not exist" in str(e) or "no such column" in str(e):
                    print("Adicionando coluna tipo_documento_id na tabela documents...")
                    db.session.execute(text("ALTER TABLE documents ADD COLUMN tipo_documento_id INTEGER"))
                    db.session.commit()
                    print("✓ Coluna tipo_documento_id adicionada na tabela documents")
            
            # 4. Criar grupos padrão se não existirem
            grupos_padrao = [
                {
                    'codigo': 'RH',
                    'nome': 'Recursos Humanos',
                    'descricao': 'Departamento de Recursos Humanos',
                    'cor': '#28a745',
                    'icone': 'bi-people'
                },
                {
                    'codigo': 'FIN',
                    'nome': 'Financeiro',
                    'descricao': 'Departamento Financeiro',
                    'cor': '#17a2b8',
                    'icone': 'bi-cash-stack'
                },
                {
                    'codigo': 'LAB',
                    'nome': 'Análises Clínicas',
                    'descricao': 'Laboratório de Análises Clínicas',
                    'cor': '#6f42c1',
                    'icone': 'bi-microscope'
                },
                {
                    'codigo': 'REC',
                    'nome': 'Recepção',
                    'descricao': 'Recepção e Atendimento',
                    'cor': '#fd7e14',
                    'icone': 'bi-person-check'
                },
                {
                    'codigo': 'QUAL',
                    'nome': 'Qualidade',
                    'descricao': 'Gestão da Qualidade',
                    'cor': '#dc3545',
                    'icone': 'bi-award'
                },
                {
                    'codigo': 'ADM',
                    'nome': 'Administração',
                    'descricao': 'Departamento Administrativo',
                    'cor': '#6c757d',
                    'icone': 'bi-building'
                }
            ]
            
            # Obter usuário administrador para criar grupos
            admin_user = User.query.filter_by(perfil='administrador').first()
            if not admin_user:
                print("Nenhum usuário administrador encontrado. Criando grupos sem criador definido.")
            
            for grupo_data in grupos_padrao:
                existing_group = Group.query.filter_by(codigo=grupo_data['codigo']).first()
                if not existing_group:
                    group = Group(
                        codigo=grupo_data['codigo'],
                        nome=grupo_data['nome'],
                        descricao=grupo_data['descricao'],
                        cor=grupo_data['cor'],
                        icone=grupo_data['icone'],
                        criado_por_id=admin_user.id if admin_user else 1
                    )
                    db.session.add(group)
                    print(f"✓ Grupo '{grupo_data['nome']}' criado.")
                else:
                    print(f"✓ Grupo '{grupo_data['nome']}' já existe.")
            
            # 5. Criar tipos de documento padrão se não existirem
            tipos_padrao = [
                {
                    'codigo': 'POL',
                    'nome': 'Política',
                    'descricao': 'Políticas organizacionais',
                    'cor': '#dc3545',
                    'icone': 'bi-shield-check'
                },
                {
                    'codigo': 'PROC',
                    'nome': 'Procedimento',
                    'descricao': 'Procedimentos operacionais',
                    'cor': '#007bff',
                    'icone': 'bi-list-check'
                },
                {
                    'codigo': 'INST',
                    'nome': 'Instrução de Trabalho',
                    'descricao': 'Instruções de trabalho detalhadas',
                    'cor': '#28a745',
                    'icone': 'bi-gear'
                },
                {
                    'codigo': 'FORM',
                    'nome': 'Formulário',
                    'descricao': 'Formulários e registros',
                    'cor': '#ffc107',
                    'icone': 'bi-file-earmark-text'
                },
                {
                    'codigo': 'MAN',
                    'nome': 'Manual',
                    'descricao': 'Manuais e guias',
                    'cor': '#6f42c1',
                    'icone': 'bi-book'
                }
            ]
            
            for tipo_data in tipos_padrao:
                existing_type = DocumentType.query.filter_by(codigo=tipo_data['codigo']).first()
                if not existing_type:
                    doc_type = DocumentType(
                        codigo=tipo_data['codigo'],
                        nome=tipo_data['nome'],
                        descricao=tipo_data['descricao'],
                        cor=tipo_data['cor'],
                        icone=tipo_data['icone'],
                        criado_por_id=admin_user.id if admin_user else 1
                    )
                    db.session.add(doc_type)
                    print(f"✓ Tipo de documento '{tipo_data['nome']}' criado.")
                else:
                    print(f"✓ Tipo de documento '{tipo_data['nome']}' já existe.")
            
            db.session.commit()
            print("\n🎉 Migração concluída com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na migração: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_database()
