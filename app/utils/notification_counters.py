"""
Sistema de contadores de notificações - Alpha Gestão Documental
Contadores em tempo real para badges na interface
"""
from flask_login import current_user
from app.models import Document, ApprovalFlow, NonConformity, Audit, CorrectiveAction
from datetime import datetime, timedelta
from app import db

def get_pending_approvals_count():
    """Contagem de aprovações pendentes para o usuário atual"""
    if not current_user.is_authenticated or not current_user.can_approve_documents():
        return 0
    
    return ApprovalFlow.query.filter_by(
        responsavel_id=current_user.id,
        status='pendente'
    ).count()

def get_expiring_documents_count():
    """Contagem de documentos vencendo (próximos 30 dias)"""
    if not current_user.is_authenticated:
        return 0
    
    data_limite = datetime.utcnow() + timedelta(days=30)
    
    # Para gestores e admins - todos os documentos
    if current_user.perfil in ['administrador', 'gestor_qualidade']:
        return Document.query.filter(
            Document.data_validade <= data_limite,
            Document.data_validade >= datetime.utcnow(),
            Document.ativo == True
        ).count()
    
    # Para outros usuários - apenas seus documentos
    return Document.query.filter(
        Document.autor_id == current_user.id,
        Document.data_validade <= data_limite,
        Document.data_validade >= datetime.utcnow(),
        Document.ativo == True
    ).count()

def get_open_nonconformities_count():
    """Contagem de não conformidades abertas atribuídas ao usuário"""
    if not current_user.is_authenticated:
        return 0
    
    count = 0
    
    # NCs onde o usuário é responsável
    count += NonConformity.query.filter_by(
        responsavel_id=current_user.id,
        status='aberta'
    ).count()
    
    # Ações corretivas atribuídas ao usuário
    count += CorrectiveAction.query.filter_by(
        responsavel_id=current_user.id,
        status='pendente'
    ).count()
    
    return count

def get_assigned_audits_count():
    """Contagem de auditorias atribuídas ao usuário"""
    if not current_user.is_authenticated:
        return 0
    
    return Audit.query.filter_by(
        auditor_lider_id=current_user.id,
        status='planejada'
    ).count() + Audit.query.filter_by(
        auditor_lider_id=current_user.id,
        status='em_andamento'
    ).count()

def get_critical_alerts_count():
    """Contagem de alertas críticos para gestores"""
    if not current_user.is_authenticated or current_user.perfil not in ['administrador', 'gestor_qualidade']:
        return 0
    
    count = 0
    
    # Documentos vencidos (já passou da data)
    count += Document.query.filter(
        Document.data_validade < datetime.utcnow(),
        Document.ativo == True
    ).count()
    
    # NCs críticas abertas
    count += NonConformity.query.filter_by(
        criticidade='critica',
        status='aberta'
    ).count()
    
    # NCs atrasadas (passou do prazo)
    count += NonConformity.query.filter(
        NonConformity.data_prazo < datetime.utcnow(),
        NonConformity.status != 'fechada'
    ).count()
    
    return count

def get_my_documents_drafts_count():
    """Contagem de rascunhos do usuário"""
    if not current_user.is_authenticated:
        return 0
    
    return Document.query.filter_by(
        autor_id=current_user.id,
        status='rascunho',
        ativo=True
    ).count()

def get_all_notification_counts():
    """Retorna todos os contadores de uma vez para otimização"""
    if not current_user.is_authenticated:
        return {
            'pending_approvals': 0,
            'expiring_documents': 0,
            'open_nonconformities': 0,
            'assigned_audits': 0,
            'critical_alerts': 0,
            'my_drafts': 0,
            'total_notifications': 0
        }
    
    counts = {
        'pending_approvals': get_pending_approvals_count(),
        'expiring_documents': get_expiring_documents_count(),
        'open_nonconformities': get_open_nonconformities_count(),
        'assigned_audits': get_assigned_audits_count(),
        'critical_alerts': get_critical_alerts_count(),
        'my_drafts': get_my_documents_drafts_count()
    }
    
    # Total de notificações importantes
    counts['total_notifications'] = (
        counts['pending_approvals'] + 
        counts['expiring_documents'] + 
        counts['open_nonconformities'] + 
        counts['assigned_audits'] + 
        counts['critical_alerts']
    )
    
    return counts

def get_notifications_summary():
    """Retorna resumo das notificações para dashboard"""
    counts = get_all_notification_counts()
    
    summary = []
    
    if counts['pending_approvals'] > 0:
        summary.append({
            'tipo': 'aprovacoes',
            'count': counts['pending_approvals'],
            'texto': f"{counts['pending_approvals']} aprovação(ões) pendente(s)",
            'url': '/approvals',
            'icon': 'bi-check-circle',
            'badge_class': 'bg-warning'
        })
    
    if counts['expiring_documents'] > 0:
        summary.append({
            'tipo': 'vencimentos',
            'count': counts['expiring_documents'],
            'texto': f"{counts['expiring_documents']} documento(s) vencendo",
            'url': '/documents?filter=expiring',
            'icon': 'bi-calendar-x',
            'badge_class': 'bg-danger'
        })
    
    if counts['open_nonconformities'] > 0:
        summary.append({
            'tipo': 'ncs',
            'count': counts['open_nonconformities'],
            'texto': f"{counts['open_nonconformities']} ação(ões) pendente(s)",
            'url': '/nonconformities',
            'icon': 'bi-exclamation-triangle',
            'badge_class': 'bg-danger'
        })
    
    if counts['assigned_audits'] > 0:
        summary.append({
            'tipo': 'auditorias',
            'count': counts['assigned_audits'],
            'texto': f"{counts['assigned_audits']} auditoria(s) ativa(s)",
            'url': '/audits',
            'icon': 'bi-clipboard-check',
            'badge_class': 'bg-info'
        })
    
    if counts['critical_alerts'] > 0:
        summary.append({
            'tipo': 'criticos',
            'count': counts['critical_alerts'],
            'texto': f"{counts['critical_alerts']} alerta(s) crítico(s)",
            'url': '/reports',
            'icon': 'bi-exclamation-diamond',
            'badge_class': 'bg-danger'
        })
    
    return summary