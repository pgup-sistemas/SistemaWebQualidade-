"""
Rotas de autenticação para o Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.ativo:
            login_user(user, remember=remember)
            flash('Login realizado com sucesso!', 'success')
            
            # Atualizar último login
            from datetime import datetime
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Email ou senha inválidos.', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Registro de novo usuário (apenas administradores)"""
    if not current_user.can_admin():
        flash('Acesso negado. Apenas administradores podem registrar usuários.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        nome_completo = request.form.get('nome_completo')
        perfil = request.form.get('perfil')
        password = request.form.get('password')
        
        # Verificar se usuário já existe
        if User.query.filter_by(email=email).first():
            flash('Este email já está em uso.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'error')
        else:
            user = User()
            user.username = username
            user.email = email
            user.nome_completo = nome_completo
            user.perfil = perfil
            user.ativo = True
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('dashboard.users'))
    
    return render_template('auth/register.html')