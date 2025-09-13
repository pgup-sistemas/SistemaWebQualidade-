"""
Rotas de autenticação para o Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from app.utils.notifications import create_notification
from app.utils.password_validator import PasswordValidator
from app.utils.audit_logger import log_user_action

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
            
            # Log de auditoria
            log_user_action('login', usuario_id=user.id)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            # Log de tentativa de login falhou
            log_user_action('login_failed', detalhes={'email': email}, status='falha', usuario_id=None)
            flash('Email ou senha inválidos.', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    # Log antes de fazer logout
    log_user_action('logout')
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

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitação de reset de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email, ativo=True).first()
        
        if user:
            # Gerar token de reset
            token = user.generate_reset_token()
            db.session.commit()
            
            # Enviar email com link de reset
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            conteudo = f"""
            <h2>Reset de Senha - Alpha Gestão Documental</h2>
            <p>Olá {user.nome_completo},</p>
            <p>Você solicitou um reset de senha para sua conta.</p>
            <p><strong>Clique no link abaixo para redefinir sua senha:</strong></p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Redefinir Senha</a></p>
            <p><small>Este link é válido por 1 hora.</small></p>
            <p>Se você não solicitou este reset, ignore este email.</p>
            <br>
            <p>Equipe Alpha Gestão Documental</p>
            """
            
            create_notification(
                user.id,
                'password_reset',
                'Reset de Senha Solicitado',
                conteudo
            )
            
        # Sempre mostrar sucesso (segurança)
        flash('Se o email existir, você receberá as instruções para reset de senha.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Efetuar reset de senha com token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Token de reset inválido ou expirado.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não conferem.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Validar nova senha com validador robusto
        is_valid, errors = PasswordValidator.validate_password(password, user.username, user.email)
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Atualizar senha e limpar token
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()
        
        # Log de auditoria
        log_user_action('password_reset', 'user', user.id, usuario_id=user.id)
        
        flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil do usuário logado"""
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo')
        email = request.form.get('email')
        username = request.form.get('username')
        
        # Validar email único (exceto o próprio usuário)
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != current_user.id:
            flash('Este email já está em uso por outro usuário.', 'error')
            return render_template('auth/profile.html')
        
        # Validar username único (exceto o próprio usuário)
        existing_username = User.query.filter_by(username=username).first()
        if existing_username and existing_username.id != current_user.id:
            flash('Este nome de usuário já está em uso.', 'error')
            return render_template('auth/profile.html')
        
        # Atualizar dados
        current_user.nome_completo = nome_completo
        current_user.email = email
        current_user.username = username
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Alterar senha do usuário logado"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verificar senha atual
        if not current_user.check_password(current_password):
            flash('Senha atual incorreta.', 'error')
            return render_template('auth/change_password.html')
        
        # Verificar confirmação
        if new_password != confirm_password:
            flash('As senhas não conferem.', 'error')
            return render_template('auth/change_password.html')
        
        # Validar nova senha com validador robusto
        is_valid, errors = PasswordValidator.validate_password(new_password, current_user.username, current_user.email)
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        # Verificar se nova senha é diferente da atual
        if current_user.check_password(new_password):
            flash('A nova senha deve ser diferente da senha atual.', 'error')
            return render_template('auth/change_password.html')
        
        # Atualizar senha
        current_user.set_password(new_password)
        db.session.commit()
        
        # Log de auditoria
        log_user_action('change_password', 'user', current_user.id)
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')