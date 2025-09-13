"""
Utilitário para logs de auditoria do Sistema Alpha Gestão Documental
"""
from flask import request
from flask_login import current_user
import json


def log_user_action(acao, recurso=None, recurso_id=None, detalhes=None, status='sucesso', usuario_id=None):
    """
    Registra uma ação do usuário no log de auditoria
    
    Args:
        acao: Tipo de ação (login, create_user, update_password, etc.)
        recurso: Tipo de recurso afetado (user, document, etc.)
        recurso_id: ID do recurso afetado
        detalhes: Detalhes adicionais (dict será convertido para JSON)
        status: Status da ação (sucesso, falha, erro)
        usuario_id: ID do usuário (usar current_user se None)
    """
    try:
        # Importar aqui para evitar importação circular
        from app.models import AuditLog
        
        # Obter ID do usuário
        if usuario_id is None and current_user.is_authenticated:
            usuario_id = current_user.id
        
        # Obter dados da requisição
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent', '')[:500]  # Limitar tamanho
        
        # Converter detalhes para JSON se for dict
        if isinstance(detalhes, dict):
            detalhes = json.dumps(detalhes, ensure_ascii=False)
        
        # Registrar log
        AuditLog.registrar_acao(
            usuario_id=usuario_id,
            acao=acao,
            recurso=recurso,
            recurso_id=recurso_id,
            detalhes=detalhes,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        
    except Exception as e:
        # Log de auditoria não deve quebrar a aplicação
        from flask import current_app
        current_app.logger.error(f"Erro ao registrar log de auditoria: {str(e)}")