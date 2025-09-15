
"""
Rotas para gestão de tipos de documentos dinâmicos
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import DocumentType, AuditLog
import re

bp = Blueprint('document_types', __name__, url_prefix='/document-types')

@bp.route('/')
@login_required
def index():
    """Lista de tipos de documentos"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('documents.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = DocumentType.query.filter_by(ativo=True)
    
    if search:
        query = query.filter(
            db.or_(
                DocumentType.codigo.contains(search),
                DocumentType.nome.contains(search)
            )
        )
    
    document_types = query.order_by(DocumentType.nome).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('document_types/index.html', 
                         document_types=document_types, 
                         search=search)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo tipo de documento"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('documents.index'))
    
    if request.method == 'POST':
        try:
            nome = request.form['nome'].strip()
            codigo = request.form['codigo'].strip().upper()
            descricao = request.form.get('descricao', '').strip()
            cor = request.form.get('cor', '#007bff')
            icone = request.form.get('icone', 'bi-file-text')
            
            # Validar código (apenas letras, números e hífen)
            if not re.match(r'^[A-Z0-9-]+$', codigo):
                flash('Código deve conter apenas letras maiúsculas, números e hífens.', 'error')
                return render_template('document_types/create.html')
            
            # Verificar se código já existe
            if DocumentType.query.filter_by(codigo=codigo).first():
                flash('Código já existe. Escolha outro código.', 'error')
                return render_template('document_types/create.html')
            
            document_type = DocumentType(
                codigo=codigo,
                nome=nome,
                descricao=descricao,
                cor=cor,
                icone=icone,
                criado_por_id=current_user.id
            )
            
            db.session.add(document_type)
            db.session.commit()
            
            # Log de auditoria
            AuditLog.registrar_acao(
                usuario_id=current_user.id,
                acao='CRIAR_TIPO_DOCUMENTO',
                recurso='document_type',
                recurso_id=document_type.id,
                detalhes=f'Tipo de documento criado: {codigo} - {nome}',
                ip_address=request.remote_addr
            )
            
            flash('Tipo de documento criado com sucesso!', 'success')
            return redirect(url_for('document_types.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tipo de documento: {str(e)}', 'error')
    
    return render_template('document_types/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar tipo de documento"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('documents.index'))
    
    document_type = DocumentType.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            document_type.nome = request.form['nome'].strip()
            document_type.descricao = request.form.get('descricao', '').strip()
            document_type.cor = request.form.get('cor', '#007bff')
            document_type.icone = request.form.get('icone', 'bi-file-text')
            
            db.session.commit()
            
            # Log de auditoria
            AuditLog.registrar_acao(
                usuario_id=current_user.id,
                acao='EDITAR_TIPO_DOCUMENTO',
                recurso='document_type',
                recurso_id=document_type.id,
                detalhes=f'Tipo de documento editado: {document_type.codigo} - {document_type.nome}',
                ip_address=request.remote_addr
            )
            
            flash('Tipo de documento atualizado com sucesso!', 'success')
            return redirect(url_for('document_types.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tipo de documento: {str(e)}', 'error')
    
    return render_template('document_types/edit.html', document_type=document_type)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Excluir tipo de documento"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('documents.index'))
    
    document_type = DocumentType.query.get_or_404(id)
    
    # Verificar se há documentos usando este tipo
    if document_type.documentos:
        flash('Não é possível excluir este tipo pois existem documentos associados.', 'error')
        return redirect(url_for('document_types.index'))
    
    try:
        document_type.ativo = False
        db.session.commit()
        
        # Log de auditoria
        AuditLog.registrar_acao(
            usuario_id=current_user.id,
            acao='EXCLUIR_TIPO_DOCUMENTO',
            recurso='document_type',
            recurso_id=document_type.id,
            detalhes=f'Tipo de documento excluído: {document_type.codigo} - {document_type.nome}',
            ip_address=request.remote_addr
        )
        
        flash('Tipo de documento excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tipo de documento: {str(e)}', 'error')
    
    return redirect(url_for('document_types.index'))

@bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """API para criar tipo de documento via AJAX"""
    if not current_user.can_create_documents():
        return jsonify({'success': False, 'error': 'Acesso negado'})
    
    try:
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip().upper()
        
        if not nome or not codigo:
            return jsonify({'success': False, 'error': 'Nome e código são obrigatórios'})
        
        # Validar código
        if not re.match(r'^[A-Z0-9-]+$', codigo):
            return jsonify({'success': False, 'error': 'Código inválido'})
        
        # Verificar duplicatas
        if DocumentType.query.filter_by(codigo=codigo).first():
            return jsonify({'success': False, 'error': 'Código já existe'})
        
        document_type = DocumentType(
            codigo=codigo,
            nome=nome,
            criado_por_id=current_user.id
        )
        
        db.session.add(document_type)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': document_type.id,
            'codigo': document_type.codigo,
            'nome': document_type.nome
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
