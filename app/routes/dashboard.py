"""
Rotas do dashboard principal - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Document, User, NonConformity, Audit, ApprovalFlow
from app import db
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard principal"""
    # Estatísticas gerais
    total_documentos = Document.query.count()
    documentos_vencidos = Document.query.filter(
        Document.data_validade < datetime.utcnow(),
        Document.ativo == True
    ).count()

    # Documentos recentes do usuário
    meus_documentos = Document.query.filter_by(
        autor_id=current_user.id
    ).order_by(Document.data_criacao.desc()).limit(5).all()

    # Aprovações pendentes para o usuário
    minhas_aprovacoes = ApprovalFlow.query.filter_by(
        responsavel_id=current_user.id,
        status='pendente'
    ).order_by(ApprovalFlow.data_atribuicao.desc()).limit(5).all()

    # Documentos mais lidos (últimos 30 dias)
    data_limite = datetime.utcnow() - timedelta(days=30)
    docs_mais_lidos = db.session.query(
        Document,
        db.func.count(Document.id).label('leituras')
    ).join(Document.leituras).filter(
        Document.ativo == True
    ).group_by(Document.id).order_by(
        db.func.count(Document.id).desc()
    ).limit(5).all()

    return render_template('dashboard/index.html',
                         total_documentos=total_documentos,
                         documentos_vencidos=documentos_vencidos,
                         meus_documentos=meus_documentos,
                         minhas_aprovacoes=minhas_aprovacoes,
                         docs_mais_lidos=docs_mais_lidos)

@bp.route('/users')
@login_required
def users():
    """Redirecionar para gestão de usuários"""
    return redirect(url_for('users.index'))

@bp.route('/reports')
@login_required
def reports():
    """Redirecionar para dashboard de relatórios"""
    return redirect(url_for('reports.index'))