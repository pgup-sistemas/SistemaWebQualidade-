"""
Rotas para gestão de usuários - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import User
from app import db
from datetime import datetime

bp = Blueprint('users', __name__)

@bp.route('/')
@login_required
def index():
    """Lista de usuários"""
    if not current_user.can_admin():
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    perfil = request.args.get('perfil', '')
    ativo = request.args.get('ativo', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.nome_completo.contains(search)) |
            (User.username.contains(search)) |
            (User.email.contains(search))
        )
    
    if perfil:
        query = query.filter_by(perfil=perfil)
        
    if ativo:
        query = query.filter_by(ativo=ativo == 'true')
    
    users = query.order_by(User.data_criacao.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    total_ativos = User.query.filter_by(ativo=True).count()
    total_inativos = User.query.filter_by(ativo=False).count()
    total_admins = User.query.filter_by(perfil='administrador').count()
    
    return render_template('users/index.html', 
                         users=users,
                         search=search,
                         current_perfil=perfil,
                         current_ativo=ativo,
                         total_ativos=total_ativos,
                         total_inativos=total_inativos,
                         total_admins=total_admins)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo usuário"""
    if not current_user.can_admin():
        flash('Você não tem permissão para criar usuários.', 'error')
        return redirect(url_for('users.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        nome_completo = request.form.get('nome_completo')
        perfil = request.form.get('perfil')
        password = request.form.get('password')
        ativo = request.form.get('ativo') == 'on'
        
        # Validações
        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já existe.', 'error')
            return render_template('users/create.html')
            
        if User.query.filter_by(email=email).first():
            flash('Este email já está em uso.', 'error')
            return render_template('users/create.html')
        
        user = User(
            username=username,
            email=email,
            nome_completo=nome_completo,
            perfil=perfil,
            ativo=ativo,
            data_criacao=datetime.utcnow()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuário {nome_completo} criado com sucesso!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/create.html')

@bp.route('/<int:id>')
@login_required 
def view(id):
    """Visualizar usuário"""
    if not current_user.can_admin():
        flash('Você não tem permissão para visualizar usuários.', 'error')
        return redirect(url_for('users.index'))
        
    user = User.query.get_or_404(id)
    return render_template('users/view.html', user=user)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar usuário"""
    if not current_user.can_admin():
        flash('Você não tem permissão para editar usuários.', 'error')
        return redirect(url_for('users.index'))
        
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        nome_completo = request.form.get('nome_completo')
        perfil = request.form.get('perfil')
        ativo = request.form.get('ativo') == 'on'
        password = request.form.get('password')
        
        # Validar username único (exceto o próprio usuário)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Este nome de usuário já existe.', 'error')
            return render_template('users/edit.html', user=user)
            
        # Validar email único (exceto o próprio usuário)
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            flash('Este email já está em uso.', 'error')
            return render_template('users/edit.html', user=user)
        
        user.username = username
        user.email = email
        user.nome_completo = nome_completo
        user.perfil = perfil
        user.ativo = ativo
        
        # Atualizar senha se fornecida
        if password:
            user.set_password(password)
        
        db.session.commit()
        
        flash(f'Usuário {nome_completo} atualizado com sucesso!', 'success')
        return redirect(url_for('users.view', id=user.id))
    
    return render_template('users/edit.html', user=user)

@bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_status(id):
    """Ativar/desativar usuário"""
    if not current_user.can_admin():
        flash('Você não tem permissão para alterar status de usuários.', 'error')
        return redirect(url_for('users.index'))
        
    user = User.query.get_or_404(id)
    
    # Não permitir desativar o próprio usuário
    if user.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'error')
        return redirect(url_for('users.index'))
    
    user.ativo = not user.ativo
    db.session.commit()
    
    status = 'ativado' if user.ativo else 'desativado'
    flash(f'Usuário {user.nome_completo} {status} com sucesso!', 'success')
    
    return redirect(url_for('users.index'))

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Excluir usuário"""
    if not current_user.can_admin():
        flash('Você não tem permissão para excluir usuários.', 'error')
        return redirect(url_for('users.index'))
        
    user = User.query.get_or_404(id)
    
    # Não permitir excluir o próprio usuário
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta.', 'error')
        return redirect(url_for('users.index'))
    
    # Verificar se o usuário tem documentos associados
    if user.documentos_criados or user.aprovacoes:
        flash('Não é possível excluir este usuário pois possui documentos ou aprovações associadas.', 'error')
        return redirect(url_for('users.index'))
    
    nome = user.nome_completo
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuário {nome} excluído com sucesso!', 'success')
    return redirect(url_for('users.index'))