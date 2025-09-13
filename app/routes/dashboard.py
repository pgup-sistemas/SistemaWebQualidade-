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
    """Dashboard principal com KPIs avançados"""
    # Estatísticas gerais
    total_documentos = Document.query.count()
    documentos_vencidos = Document.query.filter(
        Document.data_validade < datetime.utcnow(),
        Document.ativo == True
    ).count()
    
    # Documentos vencendo (próximos 30 dias)
    data_limite_30 = datetime.utcnow() + timedelta(days=30)
    documentos_vencendo = Document.query.filter(
        Document.data_validade <= data_limite_30,
        Document.data_validade >= datetime.utcnow(),
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
    from app.models import DocumentReading
    docs_mais_lidos = db.session.query(
        Document,
        db.func.count(DocumentReading.id).label('leituras')
    ).join(DocumentReading, Document.id == DocumentReading.documento_id).filter(
        Document.ativo == True,
        DocumentReading.data_leitura >= data_limite
    ).group_by(Document.id).order_by(
        db.func.count(DocumentReading.id).desc()
    ).limit(5).all()
    
    # === DADOS PARA GRÁFICOS ===
    
    # 1. Gráfico de Status dos Documentos (Doughnut)
    documentos_por_status = db.session.query(
        Document.status,
        db.func.count(Document.id).label('count')
    ).filter(Document.ativo == True).group_by(Document.status).all()
    
    # 2. Gráfico de Documentos por Mês (últimos 12 meses) - Line Chart
    data_12_meses = datetime.utcnow() - timedelta(days=365)
    documentos_por_mes = db.session.query(
        db.func.date_trunc('month', Document.data_criacao).label('mes'),
        db.func.count(Document.id).label('count')
    ).filter(
        Document.data_criacao >= data_12_meses,
        Document.ativo == True
    ).group_by(db.func.date_trunc('month', Document.data_criacao)).order_by(db.func.date_trunc('month', Document.data_criacao)).all()
    
    # 3. Gráfico de Tipos de Documento (Bar Chart)
    documentos_por_tipo = db.session.query(
        Document.tipo,
        db.func.count(Document.id).label('count')
    ).filter(Document.ativo == True).group_by(Document.tipo).order_by(db.func.count(Document.id).desc()).limit(10).all()
    
    # 4. KPIs de Qualidade
    from app.models import NonConformity, Audit
    ncs_abertas = NonConformity.query.filter_by(status='aberta').count()
    ncs_criticas = NonConformity.query.filter_by(status='aberta', criticidade='critica').count()
    auditorias_ativas = Audit.query.filter(Audit.status.in_(['planejada', 'em_andamento'])).count()
    
    # 5. Atividade dos últimos 7 dias
    data_7_dias = datetime.utcnow() - timedelta(days=7)
    atividade_7_dias = []
    for i in range(7):
        dia = data_7_dias + timedelta(days=i)
        dia_inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        dia_fim = dia_inicio + timedelta(days=1)
        
        docs_criados = Document.query.filter(
            Document.data_criacao >= dia_inicio,
            Document.data_criacao < dia_fim
        ).count()
        
        leituras = DocumentReading.query.filter(
            DocumentReading.data_leitura >= dia_inicio,
            DocumentReading.data_leitura < dia_fim
        ).count()
        
        atividade_7_dias.append({
            'dia': dia.strftime('%d/%m'),
            'docs_criados': docs_criados,
            'leituras': leituras
        })

    return render_template('dashboard/index.html',
                         total_documentos=total_documentos,
                         documentos_vencidos=documentos_vencidos,
                         documentos_vencendo=documentos_vencendo,
                         meus_documentos=meus_documentos,
                         minhas_aprovacoes=minhas_aprovacoes,
                         docs_mais_lidos=docs_mais_lidos,
                         # Dados para gráficos
                         documentos_por_status=documentos_por_status,
                         documentos_por_mes=documentos_por_mes,
                         documentos_por_tipo=documentos_por_tipo,
                         ncs_abertas=ncs_abertas,
                         ncs_criticas=ncs_criticas,
                         auditorias_ativas=auditorias_ativas,
                         atividade_7_dias=atividade_7_dias)

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