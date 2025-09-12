"""
Rotas do dashboard para o Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Document, User, ApprovalFlow, DocumentReading
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Página principal do dashboard"""
    # Estatísticas gerais
    total_documentos = Document.query.filter_by(ativo=True).count()
    documentos_vencidos = Document.query.filter(
        Document.data_validade < datetime.utcnow(),
        Document.ativo == True
    ).count()
    documentos_vencendo = Document.query.filter(
        Document.data_validade.between(
            datetime.utcnow(),
            datetime.utcnow() + timedelta(days=30)
        ),
        Document.ativo == True
    ).count()
    
    # Pendências do usuário
    if current_user.can_approve_documents():
        aprovacoes_pendentes = ApprovalFlow.query.filter_by(
            responsavel_id=current_user.id,
            status='pendente'
        ).count()
    else:
        aprovacoes_pendentes = 0
    
    # Documentos recentes
    documentos_recentes = Document.query.filter_by(ativo=True)\
        .order_by(Document.data_criacao.desc())\
        .limit(5).all()
    
    # Documentos mais lidos
    documentos_populares = db.session.query(Document, func.count(DocumentReading.id).label('leituras'))\
        .join(DocumentReading)\
        .filter(Document.ativo == True)\
        .group_by(Document.id)\
        .order_by(func.count(DocumentReading.id).desc())\
        .limit(5).all()
    
    return render_template('dashboard/index.html',
                         total_documentos=total_documentos,
                         documentos_vencidos=documentos_vencidos,
                         documentos_vencendo=documentos_vencendo,
                         aprovacoes_pendentes=aprovacoes_pendentes,
                         documentos_recentes=documentos_recentes,
                         documentos_populares=documentos_populares)

@bp.route('/users')
@login_required
def users():
    """Gestão de usuários (apenas administradores)"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.nome_completo).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('dashboard/users.html', users=users)

@bp.route('/reports')
@login_required
def reports():
    """Página de relatórios"""
    return render_template('dashboard/reports.html')