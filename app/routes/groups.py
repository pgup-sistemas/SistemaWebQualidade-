
"""
Rotas para gestão de grupos/setores - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Group, User, DocumentType, AuditLog
import re

bp = Blueprint('groups', __name__, url_prefix='/groups')

@bp.route('/')
@login_required
def index():
    """Lista de grupos/setores"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Group.query.filter_by(ativo=True)
    
    if search:
        query = query.filter(
            db.or_(
                Group.codigo.contains(search),
                Group.nome.contains(search)
            )
        )
    
    groups = query.order_by(Group.nome).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('groups/index.html', 
                         groups=groups, 
                         search=search)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo grupo/setor"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('groups.index'))
    
    if request.method == 'POST':
        try:
            nome = request.form['nome'].strip()
            codigo = request.form['codigo'].strip().upper()
            descricao = request.form.get('descricao', '').strip()
            cor = request.form.get('cor', '#28a745')
            icone = request.form.get('icone', 'bi-people')
            responsavel_id = request.form.get('responsavel_id')
            notificar_novos_documentos = request.form.get('notificar_novos_documentos') == 'on'
            
            # Validar código (apenas letras, números e hífen)
            if not re.match(r'^[A-Z0-9-]+$', codigo):
                flash('Código deve conter apenas letras maiúsculas, números e hífens.', 'error')
                return render_template('groups/create.html', users=get_potential_responsaveis())
            
            # Verificar se código já existe
            if Group.query.filter_by(codigo=codigo).first():
                flash('Código já existe. Escolha outro código.', 'error')
                return render_template('groups/create.html', users=get_potential_responsaveis())
            
            group = Group(
                codigo=codigo,
                nome=nome,
                descricao=descricao,
                cor=cor,
                icone=icone,
                responsavel_id=int(responsavel_id) if responsavel_id else None,
                notificar_novos_documentos=notificar_novos_documentos,
                criado_por_id=current_user.id
            )
            
            db.session.add(group)
            db.session.commit()
            
            # Log de auditoria
            AuditLog.registrar_acao(
                usuario_id=current_user.id,
                acao='CRIAR_GRUPO',
                recurso='group',
                recurso_id=group.id,
                detalhes=f'Grupo criado: {codigo} - {nome}',
                ip_address=request.remote_addr
            )
            
            flash('Grupo/setor criado com sucesso!', 'success')
            return redirect(url_for('groups.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar grupo: {str(e)}', 'error')
    
    return render_template('groups/create.html', users=get_potential_responsaveis())

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar grupo/setor"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('groups.index'))
    
    group = Group.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            group.nome = request.form['nome'].strip()
            group.descricao = request.form.get('descricao', '').strip()
            group.cor = request.form.get('cor', '#28a745')
            group.icone = request.form.get('icone', 'bi-people')
            responsavel_id = request.form.get('responsavel_id')
            group.responsavel_id = int(responsavel_id) if responsavel_id else None
            group.notificar_novos_documentos = request.form.get('notificar_novos_documentos') == 'on'
            
            # Gerenciar tipos de documentos associados
            document_types_ids = request.form.getlist('document_types')
            group.tipos_documentos.clear()
            for doc_type_id in document_types_ids:
                doc_type = DocumentType.query.get(int(doc_type_id))
                if doc_type:
                    group.tipos_documentos.append(doc_type)
            
            db.session.commit()
            
            # Log de auditoria
            AuditLog.registrar_acao(
                usuario_id=current_user.id,
                acao='EDITAR_GRUPO',
                recurso='group',
                recurso_id=group.id,
                detalhes=f'Grupo editado: {group.codigo} - {group.nome}',
                ip_address=request.remote_addr
            )
            
            flash('Grupo/setor atualizado com sucesso!', 'success')
            return redirect(url_for('groups.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar grupo: {str(e)}', 'error')
    
    return render_template('groups/edit.html', 
                         group=group, 
                         users=get_potential_responsaveis(),
                         document_types=DocumentType.query.filter_by(ativo=True).all())

@bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar grupo/setor"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('groups.index'))
    
    group = Group.query.get_or_404(id)
    users = User.query.filter_by(grupo_id=id, ativo=True).all()
    
    return render_template('groups/view.html', group=group, users=users)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Excluir grupo/setor"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('groups.index'))
    
    group = Group.query.get_or_404(id)
    
    # Verificar se há usuários no grupo
    if group.get_users_count() > 0:
        flash('Não é possível excluir este grupo pois existem usuários associados.', 'error')
        return redirect(url_for('groups.view', id=id))
    
    try:
        group.ativo = False
        db.session.commit()
        
        # Log de auditoria
        AuditLog.registrar_acao(
            usuario_id=current_user.id,
            acao='EXCLUIR_GRUPO',
            recurso='group',
            recurso_id=group.id,
            detalhes=f'Grupo excluído: {group.codigo} - {group.nome}',
            ip_address=request.remote_addr
        )
        
        flash('Grupo/setor excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir grupo: {str(e)}', 'error')
    
    return redirect(url_for('groups.index'))

@bp.route('/api/get-groups', methods=['GET'])
@login_required
def api_get_groups():
    """API para obter lista de grupos"""
    groups = Group.query.filter_by(ativo=True).order_by(Group.nome).all()
    return jsonify([{
        'id': g.id,
        'codigo': g.codigo,
        'nome': g.nome,
        'cor': g.cor,
        'icone': g.icone
    } for g in groups])

def get_potential_responsaveis():
    """Obter usuários que podem ser responsáveis por grupos"""
    return User.query.filter(
        User.perfil.in_(['administrador', 'gestor_qualidade', 'aprovador_revisor']),
        User.ativo == True
    ).order_by(User.nome_completo).all()
