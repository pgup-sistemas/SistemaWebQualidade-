"""
Rotas para assinatura digital de documentos - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import Document, DocumentSignature
from app.utils.signatures import DigitalSignatureManager
from app import db
import json

bp = Blueprint('signatures', __name__)

@bp.route('/document/<int:document_id>/sign', methods=['POST'])
@login_required
def sign_document(document_id):
    """Assinar documento digitalmente"""
    document = Document.query.get_or_404(document_id)
    
    # Verificar se usuário pode assinar
    if not current_user.can_approve_documents():
        return jsonify({
            'success': False, 
            'message': 'Você não tem permissão para assinar documentos.'
        }), 403
    
    signature_type = request.form.get('signature_type', 'eletronica')
    
    signature, message = DigitalSignatureManager.create_simple_signature(
        document_id=document_id,
        user_id=current_user.id,
        signature_type=signature_type
    )
    
    if signature:
        return jsonify({
            'success': True,
            'message': message,
            'signature_id': signature.id
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400

@bp.route('/document/<int:document_id>/signatures')
@login_required
def document_signatures(document_id):
    """Listar assinaturas de um documento"""
    document = Document.query.get_or_404(document_id)
    signatures = DigitalSignatureManager.get_document_signatures(document_id)
    
    return render_template('signatures/document_signatures.html',
                         document=document,
                         signatures=signatures)

@bp.route('/verify/<int:signature_id>')
def verify_signature(signature_id):
    """Verificar validade de uma assinatura (acesso público)"""
    is_valid, message = DigitalSignatureManager.verify_signature(signature_id)
    
    signature = DocumentSignature.query.get_or_404(signature_id)
    certificate_data, cert_message = DigitalSignatureManager.export_signature_certificate(signature_id)
    
    return render_template('signatures/verify.html',
                         signature=signature,
                         is_valid=is_valid,
                         message=message,
                         certificate_data=certificate_data)

@bp.route('/certificate/<int:signature_id>')
@login_required
def export_certificate(signature_id):
    """Exportar certificado de assinatura"""
    certificate_data, message = DigitalSignatureManager.export_signature_certificate(signature_id)
    
    if certificate_data:
        return jsonify({
            'success': True,
            'certificate': certificate_data
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 404

@bp.route('/document/<int:document_id>/require_signatures', methods=['POST'])
@login_required
def require_signatures(document_id):
    """Solicitar assinaturas de usuários específicos"""
    if not current_user.can_admin():
        return jsonify({
            'success': False,
            'message': 'Acesso negado.'
        }), 403
    
    user_ids = request.json.get('user_ids', [])
    signature_type = request.json.get('signature_type', 'eletronica')
    
    success, message = DigitalSignatureManager.require_signature(
        document_id=document_id,
        users_list=user_ids,
        signature_type=signature_type
    )
    
    return jsonify({
        'success': success,
        'message': message
    })

@bp.route('/my_signatures')
@login_required
def my_signatures():
    """Minhas assinaturas realizadas"""
    page = request.args.get('page', 1, type=int)
    
    signatures = DocumentSignature.query.filter_by(usuario_id=current_user.id)\
        .order_by(DocumentSignature.data_assinatura.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('signatures/my_signatures.html', signatures=signatures)