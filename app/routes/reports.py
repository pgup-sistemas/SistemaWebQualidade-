"""
Rotas para dashboard de relatórios - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Document, User, NonConformity, Audit, ApprovalFlow
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('reports', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard de relatórios"""
    # Documentos
    total_documentos = Document.query.count()
    documentos_ativos = Document.query.filter_by(ativo=True).count()
    documentos_aprovados = Document.query.filter_by(status='aprovado').count()
    documentos_rascunho = Document.query.filter_by(status='rascunho').count()
    
    # Usuários
    total_usuarios = User.query.count()
    usuarios_ativos = User.query.filter_by(ativo=True).count()
    
    # Aprovações
    aprovacoes_pendentes = ApprovalFlow.query.filter_by(status='pendente').count()
    aprovacoes_atrasadas = ApprovalFlow.query.filter(
        ApprovalFlow.data_atribuicao < datetime.utcnow() - timedelta(days=7),
        ApprovalFlow.status == 'pendente'
    ).count()
    
    # Não conformidades
    ncs_abertas = NonConformity.query.filter_by(status='aberta').count()
    ncs_criticas = NonConformity.query.filter_by(criticidade='critica').count()
    ncs_atrasadas = NonConformity.query.filter(
        NonConformity.data_prazo < datetime.utcnow(),
        NonConformity.status != 'fechada'
    ).count()
    
    # Auditorias
    auditorias_ativas = Audit.query.filter(
        Audit.status.in_(['planejada', 'em_andamento'])
    ).count()
    auditorias_concluidas = Audit.query.filter_by(status='concluida').count()
    
    # Atividades recentes (últimos 30 dias)
    data_limite = datetime.utcnow() - timedelta(days=30)
    documentos_criados_mes = Document.query.filter(
        Document.data_criacao >= data_limite
    ).count()
    ncs_abertas_mes = NonConformity.query.filter(
        NonConformity.data_abertura >= data_limite
    ).count()
    auditorias_mes = Audit.query.filter(
        Audit.data_criacao >= data_limite
    ).count()
    
    # Documentos por categoria (top 5)
    categorias = db.session.query(
        Document.categoria,
        func.count(Document.id).label('count')
    ).filter_by(ativo=True).group_by(Document.categoria).order_by(
        func.count(Document.id).desc()
    ).limit(5).all()
    
    return render_template('reports/index.html',
                         total_documentos=total_documentos,
                         documentos_ativos=documentos_ativos,
                         documentos_aprovados=documentos_aprovados,
                         documentos_rascunho=documentos_rascunho,
                         total_usuarios=total_usuarios,
                         usuarios_ativos=usuarios_ativos,
                         aprovacoes_pendentes=aprovacoes_pendentes,
                         aprovacoes_atrasadas=aprovacoes_atrasadas,
                         ncs_abertas=ncs_abertas,
                         ncs_criticas=ncs_criticas,
                         ncs_atrasadas=ncs_atrasadas,
                         auditorias_ativas=auditorias_ativas,
                         auditorias_concluidas=auditorias_concluidas,
                         documentos_criados_mes=documentos_criados_mes,
                         ncs_abertas_mes=ncs_abertas_mes,
                         auditorias_mes=auditorias_mes,
                         categorias=categorias)