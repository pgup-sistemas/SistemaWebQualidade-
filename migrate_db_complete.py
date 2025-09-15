
#!/usr/bin/env python3
"""
Script completo para migrar banco de dados com grupos/setores
"""
import os
import sys
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

def migrate_database():
    """Migração completa do banco de dados sem carregar app context inicialmente"""
    try:
        print("Iniciando migração do banco de dados...")
        
        # Conectar diretamente ao banco para fazer as alterações de schema
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL não encontrada!")
            return False
            
        engine = create_engine(database_url)
        
        # Detectar tipo de banco
        is_postgres = database_url.startswith('postgresql')
        
        print("✓ Conectado ao banco de dados")
        
        # Executar cada operação em uma transação separada para PostgreSQL
        with engine.connect() as connection:
            # 1. Verificar e criar tabela groups primeiro
            try:
                result = connection.execute(text("SELECT 1 FROM groups LIMIT 1"))
                result.fetchone()
                print("✓ Tabela groups já existe")
            except:
                print("Criando tabela groups...")
                if is_postgres:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS groups (
                            id SERIAL PRIMARY KEY,
                            codigo VARCHAR(20) UNIQUE NOT NULL,
                            nome VARCHAR(100) NOT NULL,
                            descricao TEXT,
                            cor VARCHAR(7) DEFAULT '#28a745',
                            icone VARCHAR(50) DEFAULT 'bi-people',
                            responsavel_id INTEGER,
                            notificar_novos_documentos BOOLEAN DEFAULT TRUE,
                            ativo BOOLEAN DEFAULT TRUE,
                            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            criado_por_id INTEGER NOT NULL
                        )
                    """))
                else:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS groups (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            codigo VARCHAR(20) UNIQUE NOT NULL,
                            nome VARCHAR(100) NOT NULL,
                            descricao TEXT,
                            cor VARCHAR(7) DEFAULT '#28a745',
                            icone VARCHAR(50) DEFAULT 'bi-people',
                            responsavel_id INTEGER,
                            notificar_novos_documentos BOOLEAN DEFAULT 1,
                            ativo BOOLEAN DEFAULT 1,
                            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                            criado_por_id INTEGER NOT NULL
                        )
                    """))
                connection.commit()
                print("✓ Tabela groups criada")

        # 2. Verificar e adicionar colunas na tabela users
        with engine.connect() as connection:
            try:
                result = connection.execute(text("SELECT grupo_id FROM users LIMIT 1"))
                result.fetchone()
                print("✓ Coluna grupo_id já existe na tabela users")
            except:
                print("Adicionando colunas na tabela users...")
                if is_postgres:
                    connection.execute(text("ALTER TABLE users ADD COLUMN grupo_id INTEGER"))
                    connection.commit()
                    
                    try:
                        connection.execute(text("ALTER TABLE users ADD COLUMN cargo VARCHAR(100)"))
                        connection.commit()
                    except:
                        pass  # Coluna já existe
                    
                    try:
                        connection.execute(text("ALTER TABLE users ADD COLUMN receber_notificacoes BOOLEAN DEFAULT TRUE"))
                        connection.commit()
                    except:
                        pass  # Coluna já existe
                else:
                    connection.execute(text("ALTER TABLE users ADD COLUMN grupo_id INTEGER"))
                    connection.execute(text("ALTER TABLE users ADD COLUMN cargo VARCHAR(100)"))
                    connection.execute(text("ALTER TABLE users ADD COLUMN receber_notificacoes BOOLEAN DEFAULT 1"))
                    connection.commit()
                print("✓ Colunas adicionadas na tabela users")
        
        # 3. Verificar e criar tabela document_types
        with engine.connect() as connection:
            try:
                result = connection.execute(text("SELECT 1 FROM document_types LIMIT 1"))
                result.fetchone()
                print("✓ Tabela document_types já existe")
            except:
                print("Criando tabela document_types...")
                if is_postgres:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS document_types (
                            id SERIAL PRIMARY KEY,
                            codigo VARCHAR(20) UNIQUE NOT NULL,
                            nome VARCHAR(100) NOT NULL,
                            descricao TEXT,
                            cor VARCHAR(7) DEFAULT '#007bff',
                            icone VARCHAR(50) DEFAULT 'bi-file-text',
                            notificar_grupos BOOLEAN DEFAULT TRUE,
                            ativo BOOLEAN DEFAULT TRUE,
                            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            criado_por_id INTEGER NOT NULL
                        )
                    """))
                else:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS document_types (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            codigo VARCHAR(20) UNIQUE NOT NULL,
                            nome VARCHAR(100) NOT NULL,
                            descricao TEXT,
                            cor VARCHAR(7) DEFAULT '#007bff',
                            icone VARCHAR(50) DEFAULT 'bi-file-text',
                            notificar_grupos BOOLEAN DEFAULT 1,
                            ativo BOOLEAN DEFAULT 1,
                            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                            criado_por_id INTEGER NOT NULL
                        )
                    """))
                connection.commit()
                print("✓ Tabela document_types criada")
        
        # 4. Verificar e adicionar coluna tipo_documento_id na tabela documents
        with engine.connect() as connection:
            try:
                result = connection.execute(text("SELECT tipo_documento_id FROM documents LIMIT 1"))
                result.fetchone()
                print("✓ Coluna tipo_documento_id já existe na tabela documents")
            except:
                print("Adicionando coluna tipo_documento_id na tabela documents...")
                connection.execute(text("ALTER TABLE documents ADD COLUMN tipo_documento_id INTEGER"))
                connection.commit()
                print("✓ Coluna tipo_documento_id adicionada na tabela documents")

        # 5. Criar tabela de relacionamento many-to-many se não existir
        with engine.connect() as connection:
            try:
                result = connection.execute(text("SELECT 1 FROM document_type_groups LIMIT 1"))
                result.fetchone()
                print("✓ Tabela document_type_groups já existe")
            except:
                print("Criando tabela document_type_groups...")
                if is_postgres:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS document_type_groups (
                            document_type_id INTEGER NOT NULL,
                            group_id INTEGER NOT NULL,
                            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (document_type_id, group_id),
                            FOREIGN KEY (document_type_id) REFERENCES document_types(id),
                            FOREIGN KEY (group_id) REFERENCES groups(id)
                        )
                    """))
                else:
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS document_type_groups (
                            document_type_id INTEGER NOT NULL,
                            group_id INTEGER NOT NULL,
                            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (document_type_id, group_id),
                            FOREIGN KEY (document_type_id) REFERENCES document_types(id),
                            FOREIGN KEY (group_id) REFERENCES groups(id)
                        )
                    """))
                connection.commit()
                print("✓ Tabela document_type_groups criada")
        
        print("✓ Migração de schema concluída!")
        
        # Agora carregar a aplicação para popular dados
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import create_app, db
        from app.models import Group, User, DocumentType
        
        app = create_app()
        with app.app_context():
            print("Populando dados padrão...")
            
            # Criar usuário admin se não existir
            admin_user = User.query.filter_by(email='admin@alphagestao.com').first()
            if not admin_user:
                admin_user = User()
                admin_user.username = 'admin'
                admin_user.email = 'admin@alphagestao.com'
                admin_user.nome_completo = 'Administrador do Sistema'
                admin_user.perfil = 'administrador'
                admin_user.ativo = True
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Usuário administrador criado")
            
            # Criar grupos padrão
            grupos_padrao = [
                {'codigo': 'RH', 'nome': 'Recursos Humanos', 'descricao': 'Departamento de Recursos Humanos', 'cor': '#28a745', 'icone': 'bi-people'},
                {'codigo': 'FIN', 'nome': 'Financeiro', 'descricao': 'Departamento Financeiro', 'cor': '#17a2b8', 'icone': 'bi-cash-stack'},
                {'codigo': 'LAB', 'nome': 'Análises Clínicas', 'descricao': 'Laboratório de Análises Clínicas', 'cor': '#6f42c1', 'icone': 'bi-microscope'},
                {'codigo': 'REC', 'nome': 'Recepção', 'descricao': 'Recepção e Atendimento', 'cor': '#fd7e14', 'icone': 'bi-person-check'},
                {'codigo': 'QUAL', 'nome': 'Qualidade', 'descricao': 'Gestão da Qualidade', 'cor': '#dc3545', 'icone': 'bi-award'},
                {'codigo': 'ADM', 'nome': 'Administração', 'descricao': 'Departamento Administrativo', 'cor': '#6c757d', 'icone': 'bi-building'}
            ]
            
            for grupo_data in grupos_padrao:
                existing_group = Group.query.filter_by(codigo=grupo_data['codigo']).first()
                if not existing_group:
                    group = Group(
                        codigo=grupo_data['codigo'],
                        nome=grupo_data['nome'],
                        descricao=grupo_data['descricao'],
                        cor=grupo_data['cor'],
                        icone=grupo_data['icone'],
                        criado_por_id=admin_user.id
                    )
                    db.session.add(group)
                    print(f"✓ Grupo '{grupo_data['nome']}' criado")
                else:
                    print(f"✓ Grupo '{grupo_data['nome']}' já existe")
            
            # Criar tipos de documento padrão
            tipos_padrao = [
                {'codigo': 'POL', 'nome': 'Política', 'descricao': 'Políticas organizacionais', 'cor': '#dc3545', 'icone': 'bi-shield-check'},
                {'codigo': 'PROC', 'nome': 'Procedimento', 'descricao': 'Procedimentos operacionais', 'cor': '#007bff', 'icone': 'bi-list-check'},
                {'codigo': 'INST', 'nome': 'Instrução de Trabalho', 'descricao': 'Instruções de trabalho detalhadas', 'cor': '#28a745', 'icone': 'bi-gear'},
                {'codigo': 'FORM', 'nome': 'Formulário', 'descricao': 'Formulários e registros', 'cor': '#ffc107', 'icone': 'bi-file-earmark-text'},
                {'codigo': 'MAN', 'nome': 'Manual', 'descricao': 'Manuais e guias', 'cor': '#6f42c1', 'icone': 'bi-book'}
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
                        criado_por_id=admin_user.id
                    )
                    db.session.add(doc_type)
                    print(f"✓ Tipo de documento '{tipo_data['nome']}' criado")
                else:
                    print(f"✓ Tipo de documento '{tipo_data['nome']}' já existe")
            
            db.session.commit()
            print("\n🎉 Migração concluída com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro na migração: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    migrate_database()
