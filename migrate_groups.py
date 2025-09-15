
#!/usr/bin/env python3
"""
Script para migrar banco de dados com grupos/setores
"""
from app import create_app, db
from app.models import Group, User, DocumentType

def migrate_groups():
    """Criar tabelas de grupos e adicionar campos necessários"""
    app = create_app()
    
    with app.app_context():
        try:
            # Criar todas as tabelas (incluindo as novas)
            db.create_all()
            
            # Criar grupos padrão se não existirem
            default_groups = [
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
                }
            ]
            
            # Obter usuário administrador para criar grupos
            admin_user = User.query.filter_by(perfil='administrador').first()
            if not admin_user:
                print("Nenhum usuário administrador encontrado. Criando grupos sem criador definido.")
            
            for group_data in default_groups:
                existing_group = Group.query.filter_by(codigo=group_data['codigo']).first()
                if not existing_group:
                    group = Group(
                        codigo=group_data['codigo'],
                        nome=group_data['nome'],
                        descricao=group_data['descricao'],
                        cor=group_data['cor'],
                        icone=group_data['icone'],
                        criado_por_id=admin_user.id if admin_user else 1
                    )
                    db.session.add(group)
                    print(f"Grupo '{group_data['nome']}' criado.")
                else:
                    print(f"Grupo '{group_data['nome']}' já existe.")
            
            db.session.commit()
            print("Migração de grupos concluída com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro na migração: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_groups()
