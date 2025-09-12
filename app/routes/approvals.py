"""
Rotas de aprovação para o Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import ApprovalFlow, Document, User
from app import db
from datetime import datetime

bp = Blueprint('approvals', __name__)

@bp.route('/')
@login_required
def index():
    """Lista de aprovações pendentes"""
    if not current_user.can_approve_documents():
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    
    approvals = ApprovalFlow.query.filter_by(
        responsavel_id=current_user.id,
        status='pendente'
    ).join(Document).order_by(ApprovalFlow.data_atribuicao.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('approvals/index.html', approvals=approvals)

@bp.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve(id):
    """Aprovar documento"""
    approval = ApprovalFlow.query.get_or_404(id)
    
    if approval.responsavel_id != current_user.id:
        flash('Você não tem permissão para esta aprovação.', 'error')
        return redirect(url_for('approvals.index'))
    
    if approval.status != 'pendente':
        flash('Esta aprovação já foi processada.', 'warning')
        return redirect(url_for('approvals.index'))
    
    comentarios = request.form.get('comentarios', '')
    
    # Aprovar
    approval.status = 'aprovado'
    approval.data_conclusao = datetime.utcnow()
    approval.comentarios = comentarios
    
    # Verificar se é a última aprovação
    pending_approvals = ApprovalFlow.query.filter_by(
        documento_id=approval.documento_id,
        status='pendente'
    ).count()
    
    if pending_approvals == 0:
        # Todas aprovações concluídas - marcar documento como aprovado
        document = Document.query.get(approval.documento_id)
        document.status = 'aprovado'
        document.data_ultima_revisao = datetime.utcnow()
    
    db.session.commit()
    
    flash('Documento aprovado com sucesso!', 'success')
    return redirect(url_for('approvals.index'))

@bp.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject(id):
    """Rejeitar documento"""
    approval = ApprovalFlow.query.get_or_404(id)
    
    if approval.responsavel_id != current_user.id:
        flash('Você não tem permissão para esta aprovação.', 'error')
        return redirect(url_for('approvals.index'))
    
    if approval.status != 'pendente':
        flash('Esta aprovação já foi processada.', 'warning')
        return redirect(url_for('approvals.index'))
    
    comentarios = request.form.get('comentarios', '')
    
    if not comentarios.strip():
        flash('É obrigatório informar o motivo da rejeição.', 'error')
        return redirect(url_for('approvals.index'))
    
    # Rejeitar
    approval.status = 'rejeitado'
    approval.data_conclusao = datetime.utcnow()
    approval.comentarios = comentarios
    
    # Marcar documento como rejeitado (volta para rascunho)
    document = Document.query.get(approval.documento_id)
    document.status = 'rascunho'
    
    # Cancelar outras aprovações pendentes do mesmo documento
    other_approvals = ApprovalFlow.query.filter_by(
        documento_id=approval.documento_id,
        status='pendente'
    ).filter(ApprovalFlow.id != approval.id)
    
    for other_approval in other_approvals:
        other_approval.status = 'cancelado'
    
    db.session.commit()
    
    flash('Documento rejeitado e retornado para o autor.', 'info')
    return redirect(url_for('approvals.index'))

@bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar aprovação"""
    approval = ApprovalFlow.query.get_or_404(id)
    
    if approval.responsavel_id != current_user.id and not current_user.can_admin():
        flash('Você não tem permissão para visualizar esta aprovação.', 'error')
        return redirect(url_for('approvals.index'))
    
    document = approval.documento
    current_version = document.get_current_version()
    
    return render_template('approvals/view.html', 
                         approval=approval,
                         document=document,
                         current_version=current_version)