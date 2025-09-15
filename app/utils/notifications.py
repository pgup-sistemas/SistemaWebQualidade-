"""
Sistema avançado de notificações por email - Alpha Gestão Documental
"""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail, db
from app.models import EmailNotification, User, Document, NonConformity, Audit
from datetime import datetime, timedelta
import threading

def send_async_email(app, msg):
    """Enviar email de forma assíncrona"""
    with app.app_context():
        try:
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar email: {str(e)}")
            return False

def send_email(subject, recipients, text_body, html_body=None):
    """Enviar email com tratamento de erros"""
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.warning("Servidor de email não configurado")
        return False
    
    try:
        msg = Message(
            subject=f"[Alpha Gestão] {subject}",
            recipients=recipients,
            body=text_body,
            html=html_body
        )
        
        # Enviar de forma assíncrona
        thr = threading.Thread(
            target=send_async_email, 
            args=[current_app, msg]
        )
        thr.start()
        return True
        
    except Exception as e:
        current_app.logger.error(f"Erro ao preparar email: {str(e)}")
        return False

def create_notification(user_id, tipo, assunto, conteudo, entidade_tipo=None, entidade_id=None):
    """Criar notificação na fila de envio"""
    notification = EmailNotification()
    notification.destinatario_id = user_id
    notification.tipo = tipo
    notification.assunto = assunto
    notification.conteudo = conteudo
    notification.entidade_tipo = entidade_tipo
    notification.entidade_id = entidade_id
    
    db.session.add(notification)
    db.session.commit()
    
    # Tentar enviar imediatamente
    process_pending_notifications()
    
    return notification

def process_pending_notifications():
    """Processar notificações pendentes"""
    notifications = EmailNotification.query.filter_by(status='pendente').limit(10).all()
    
    for notification in notifications:
        try:
            user = notification.destinatario
            if user and user.ativo:
                success = send_email(
                    subject=notification.assunto,
                    recipients=[user.email],
                    text_body=notification.conteudo,
                    html_body=render_email_template(notification)
                )
                
                if success:
                    notification.status = 'enviado'
                    notification.data_envio = datetime.utcnow()
                else:
                    notification.status = 'erro'
                    notification.erro_mensagem = 'Falha no envio'
                    notification.tentativas += 1
            else:
                notification.status = 'erro'
                notification.erro_mensagem = 'Usuário inativo ou não encontrado'
                
        except Exception as e:
            notification.status = 'erro'
            notification.erro_mensagem = str(e)
            notification.tentativas += 1
    
    db.session.commit()

def render_email_template(notification):
    """Renderizar template HTML do email"""
    base_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; border-radius: 8px; }
            .header { background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { background: white; padding: 20px; border-radius: 0 0 8px 8px; }
            .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
            .btn { display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Alpha Gestão Documental</h2>
            </div>
            <div class="content">
                <h3>{{ assunto }}</h3>
                <p>Olá {{ nome_usuario }},</p>
                {{ conteudo_html }}
                <p>Atenciosamente,<br>Sistema Alpha Gestão Documental</p>
            </div>
            <div class="footer">
                <p>Este é um email automático. Não responda a esta mensagem.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        conteudo_html = notification.conteudo.replace('\n', '<br>')
        
        return render_template_string(
            base_template,
            assunto=notification.assunto,
            nome_usuario=notification.destinatario.nome_completo,
            conteudo_html=conteudo_html
        )
    except:
        return None

# Notificações específicas do sistema

def notify_document_created(document):
    """Notificar grupos sobre novo documento disponível"""
    if not document.tipo_documento_obj or not document.tipo_documento_obj.notificar_grupos:
        return
    
    # Obter grupos relacionados ao tipo de documento
    related_groups = document.tipo_documento_obj.get_related_groups()
    
    for group in related_groups:
        if group.notificar_novos_documentos:
            # Notificar todos os usuários ativos do grupo
            users = group.get_active_users()
            
            for user in users:
                if user.receber_notificacoes:
                    assunto = f"Novo documento disponível - {document.tipo}"
                    conteudo = f"""
Olá {user.nome_completo},

Um novo documento está disponível para seu setor ({group.nome}):

Título: {document.titulo}
Código: {document.codigo}
Tipo: {document.tipo}
Autor: {document.autor.nome_completo}

Por favor, acesse o sistema para visualizar o documento.
                    """
                    
                    create_notification(
                        user_id=user.id,
                        tipo='novo_documento_disponivel',
                        assunto=assunto,
                        conteudo=conteudo,
                        entidade_tipo='document',
                        entidade_id=document.id
                    )

def notify_document_expiring(document):
    """Notificar sobre documento próximo do vencimento"""
    if not document.data_validade:
        return
    
    days_to_expire = document.days_to_expire()
    if days_to_expire and days_to_expire <= 30:
        # Notificar autor e gestores
        users_to_notify = [document.autor]
        gestores = User.query.filter(
            User.perfil.in_(['administrador', 'gestor_qualidade']),
            User.ativo == True
        ).all()
        users_to_notify.extend(gestores)
        
        # Também notificar grupos relacionados se aplicável
        if document.tipo_documento_obj:
            for group in document.tipo_documento_obj.get_related_groups():
                if group.responsavel:
                    users_to_notify.append(group.responsavel)
        
        for user in set(users_to_notify):
            assunto = f"Documento {document.codigo} vencendo em {days_to_expire} dias"
            conteudo = f"""
O documento "{document.titulo}" (código: {document.codigo}) vencerá em {days_to_expire} dias.

Data de vencimento: {document.data_validade.strftime('%d/%m/%Y')}

Por favor, revise e atualize o documento conforme necessário.
            """
            
            create_notification(
                user_id=user.id,
                tipo='documento_vencendo',
                assunto=assunto,
                conteudo=conteudo,
                entidade_tipo='document',
                entidade_id=document.id
            )

def notify_approval_pending(approval_flow):
    """Notificar sobre aprovação pendente"""
    user = approval_flow.responsavel
    document = approval_flow.documento
    
    assunto = f"Aprovação pendente: {document.titulo}"
    conteudo = f"""
Você tem uma aprovação pendente para o documento "{document.titulo}" (código: {document.codigo}).

Etapa: {approval_flow.etapa}
Documento criado por: {document.autor.nome_completo}

Por favor, acesse o sistema para revisar e aprovar o documento.
    """
    
    create_notification(
        user_id=user.id,
        tipo='aprovacao_pendente',
        assunto=assunto,
        conteudo=conteudo,
        entidade_tipo='approval_flow',
        entidade_id=approval_flow.id
    )

def notify_nonconformity_opened(nc):
    """Notificar sobre nova não conformidade"""
    users_to_notify = []
    
    if nc.responsavel:
        users_to_notify.append(nc.responsavel)
    
    # Notificar gestores da qualidade
    gestores = User.query.filter(
        User.perfil.in_(['administrador', 'gestor_qualidade']),
        User.ativo == True
    ).all()
    users_to_notify.extend(gestores)
    
    for user in set(users_to_notify):
        assunto = f"Nova não conformidade: {nc.codigo}"
        conteudo = f"""
Uma nova não conformidade foi aberta:

Código: {nc.codigo}
Título: {nc.titulo}
Criticidade: {nc.criticidade.upper()}
Tipo: {nc.tipo.title()}

Aberta por: {nc.aberto_por.nome_completo}

Descrição:
{nc.descricao}
        """
        
        create_notification(
            user_id=user.id,
            tipo='nc_aberta',
            assunto=assunto,
            conteudo=conteudo,
            entidade_tipo='non_conformity',
            entidade_id=nc.id
        )

def notify_audit_assigned(audit):
    """Notificar sobre auditoria atribuída"""
    auditor = audit.auditor_lider
    
    assunto = f"Auditoria atribuída: {audit.titulo}"
    conteudo = f"""
Você foi designado como auditor líder para a auditoria "{audit.titulo}" (código: {audit.codigo}).

Tipo: {audit.tipo.title()}
Área auditada: {audit.area_auditada}
Período: {audit.data_inicio.strftime('%d/%m/%Y') if audit.data_inicio else 'A definir'} até {audit.data_fim.strftime('%d/%m/%Y') if audit.data_fim else 'A definir'}

Escopo:
{audit.escopo}

Por favor, acesse o sistema para planejar e executar a auditoria.
    """
    
    create_notification(
        user_id=auditor.id,
        tipo='auditoria_atribuida',
        assunto=assunto,
        conteudo=conteudo,
        entidade_tipo='audit',
        entidade_id=audit.id
    )

def notify_corrective_action_assigned(action):
    """Notificar sobre ação corretiva atribuída"""
    responsavel = action.responsavel
    nc = action.nao_conformidade
    
    assunto = f"Ação {action.tipo} atribuída - NC {nc.codigo}"
    conteudo = f"""
Uma ação {action.tipo} foi atribuída a você para a não conformidade {nc.codigo}.

Não conformidade: {nc.titulo}
Tipo da ação: {action.tipo.title()}
Prazo: {action.data_prazo.strftime('%d/%m/%Y') if action.data_prazo else 'Não definido'}

Descrição da ação:
{action.descricao}

Justificativa:
{action.justificativa or 'Não informada'}

Por favor, acesse o sistema para acompanhar e executar a ação.
    """
    
    create_notification(
        user_id=responsavel.id,
        tipo='acao_atribuida',
        assunto=assunto,
        conteudo=conteudo,
        entidade_tipo='corrective_action',
        entidade_id=action.id
    )