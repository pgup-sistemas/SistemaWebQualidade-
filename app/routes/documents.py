"""
Rotas de documentos para o Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import Document, DocumentVersion, DocumentReading, ApprovalFlow
from app import db
from datetime import datetime
import uuid

bp = Blueprint('documents', __name__)

@bp.route('/')
@login_required
def index():
    """Lista de documentos"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    tipo = request.args.get('tipo', '')
    status = request.args.get('status', '')
    
    query = Document.query.filter_by(ativo=True)
    
    if search:
        query = query.filter(
            (Document.titulo.contains(search)) |
            (Document.codigo.contains(search)) |
            (Document.palavras_chave.contains(search))
        )
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if status:
        query = query.filter_by(status=status)
    
    documents = query.order_by(Document.data_criacao.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Tipos de documento para filtro
    tipos = db.session.query(Document.tipo.distinct()).filter_by(ativo=True).all()
    tipos = [t[0] for t in tipos]
    
    return render_template('documents/index.html', 
                         documents=documents, 
                         search=search,
                         tipos=tipos,
                         current_tipo=tipo,
                         current_status=status)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo documento"""
    if not current_user.can_create_documents():
        flash('Você não tem permissão para criar documentos.', 'error')
        return redirect(url_for('documents.index'))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        tipo = request.form.get('tipo')
        departamento = request.form.get('departamento')
        palavras_chave = request.form.get('palavras_chave')
        resumo = request.form.get('resumo')
        conteudo = request.form.get('conteudo')
        data_validade = request.form.get('data_validade')
        
        # Gerar código único
        codigo = f"{tipo.upper()}-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Criar documento
        document = Document(
            codigo=codigo,
            titulo=titulo,
            tipo=tipo,
            departamento=departamento,
            palavras_chave=palavras_chave,
            resumo=resumo,
            autor_id=current_user.id,
            data_validade=datetime.strptime(data_validade, '%Y-%m-%d') if data_validade else None
        )
        
        db.session.add(document)
        db.session.flush()  # Para obter o ID
        
        # Criar primeira versão
        version = DocumentVersion(
            documento_id=document.id,
            versao='1.0',
            conteudo=conteudo,
            criado_por_id=current_user.id,
            changelog='Versão inicial'
        )
        
        db.session.add(version)
        db.session.commit()
        
        # Verificar se é para salvar como rascunho ou submeter
        action = request.form.get('action', 'submit')
        
        if action == 'draft':
            document.status = 'rascunho'
            flash(f'Rascunho "{titulo}" salvo com sucesso!', 'info')
        else:
            flash(f'Documento "{titulo}" criado com sucesso!', 'success')
        
        return redirect(url_for('documents.view', id=document.id))
    
    return render_template('documents/create.html')

@bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar documento"""
    document = Document.query.get_or_404(id)
    current_version = document.get_current_version()
    
    # Registrar leitura
    reading = DocumentReading.query.filter_by(
        documento_id=document.id,
        usuario_id=current_user.id,
        versao_lida=document.versao_atual
    ).first()
    
    if not reading:
        reading = DocumentReading(
            documento_id=document.id,
            usuario_id=current_user.id,
            versao_lida=document.versao_atual,
            ip_address=request.remote_addr
        )
        db.session.add(reading)
        db.session.commit()
    
    return render_template('documents/view.html', 
                         document=document, 
                         current_version=current_version)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar documento"""
    document = Document.query.get_or_404(id)
    
    if not (current_user.can_create_documents() or document.autor_id == current_user.id):
        flash('Você não tem permissão para editar este documento.', 'error')
        return redirect(url_for('documents.view', id=id))
    
    if document.status == 'aprovado':
        flash('Documentos aprovados não podem ser editados diretamente. Crie uma nova versão.', 'warning')
        return redirect(url_for('documents.view', id=id))
    
    current_version = document.get_current_version()
    
    if request.method == 'POST':
        # Atualizar documento
        document.titulo = request.form.get('titulo')
        document.tipo = request.form.get('tipo')
        document.departamento = request.form.get('departamento')
        document.palavras_chave = request.form.get('palavras_chave')
        document.resumo = request.form.get('resumo')
        data_validade = request.form.get('data_validade')
        document.data_validade = datetime.strptime(data_validade, '%Y-%m-%d') if data_validade else None
        
        # Atualizar conteúdo da versão atual
        conteudo = request.form.get('conteudo')
        changelog = request.form.get('changelog', 'Edição da versão atual')
        
        current_version.conteudo = conteudo
        current_version.changelog = changelog
        document.data_ultima_revisao = datetime.utcnow()
        
        db.session.commit()
        
        flash('Documento atualizado com sucesso!', 'success')
        return redirect(url_for('documents.view', id=id))
    
    return render_template('documents/edit.html', 
                         document=document, 
                         current_version=current_version)

@bp.route('/<int:id>/confirm_reading', methods=['POST'])
@login_required
def confirm_reading(id):
    """Confirmar leitura de documento via AJAX"""
    document = Document.query.get_or_404(id)
    
    # Verificar se já foi lida esta versão
    reading = DocumentReading.query.filter_by(
        documento_id=document.id,
        usuario_id=current_user.id,
        versao_lida=document.versao_atual
    ).first()
    
    if not reading:
        reading = DocumentReading(
            documento_id=document.id,
            usuario_id=current_user.id,
            versao_lida=document.versao_atual,
            ip_address=request.remote_addr
        )
        db.session.add(reading)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Leitura confirmada com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'Leitura já confirmada para esta versão.'})

@bp.route('/<int:id>/versions')
@login_required
def versions(id):
    """Histórico de versões do documento"""
    document = Document.query.get_or_404(id)
    versions = document.versoes.order_by(DocumentVersion.data_criacao.desc()).all()
    
    return render_template('documents/versions.html', 
                         document=document, 
                         versions=versions)

@bp.route('/api/save-draft', methods=['POST'])
@login_required
def save_draft():
    """API para salvar rascunho automaticamente"""
    if not current_user.can_create_documents():
        return jsonify({'success': False, 'error': 'Sem permissão'})
    
    try:
        document_id = request.form.get('document_id')
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        tipo = request.form.get('tipo', 'outros')
        departamento = request.form.get('departamento', '')
        
        if not titulo or not conteudo:
            return jsonify({'success': False, 'error': 'Título e conteúdo são obrigatórios'})
        
        if document_id:
            # Atualizar documento existente
            document = Document.query.get(document_id)
            if document and document.autor_id == current_user.id and document.status == 'rascunho':
                document.titulo = titulo
                document.data_modificacao = datetime.utcnow()
                
                # Atualizar versão atual
                current_version = document.get_current_version()
                if current_version:
                    current_version.conteudo = conteudo
                    current_version.data_modificacao = datetime.utcnow()
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Rascunho atualizado', 'document_id': document.id})
        else:
            # Criar novo rascunho
            codigo = f"{tipo.upper()}-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:8].upper()}"
            
            document = Document(
                codigo=codigo,
                titulo=titulo,
                tipo=tipo,
                departamento=departamento,
                autor_id=current_user.id,
                status='rascunho'
            )
            
            db.session.add(document)
            db.session.flush()  # Para obter o ID
            
            # Criar primeira versão
            version = DocumentVersion(
                documento_id=document.id,
                versao='1.0',
                conteudo=conteudo,
                criado_por_id=current_user.id,
                changelog='Rascunho inicial'
            )
            
            db.session.add(version)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Novo rascunho criado', 'document_id': document.id})
        
        return jsonify({'success': False, 'error': 'Documento não encontrado'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/drafts')
@login_required
def drafts():
    """Lista de rascunhos do usuário"""
    if not current_user.can_create_documents():
        flash('Você não tem permissão para ver rascunhos.', 'error')
        return redirect(url_for('documents.index'))
    
    page = request.args.get('page', 1, type=int)
    
    drafts = Document.query.filter_by(
        autor_id=current_user.id,
        status='rascunho',
        ativo=True
    ).order_by(Document.data_ultima_revisao.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('documents/drafts.html', drafts=drafts)

@bp.route('/<int:id>/restore-version/<int:version_id>', methods=['POST'])
@login_required
def restore_version(id, version_id):
    """Restaurar uma versão específica do documento"""
    document = Document.query.get_or_404(id)
    version = DocumentVersion.query.get_or_404(version_id)
    
    if not (current_user.can_create_documents() or document.autor_id == current_user.id):
        return jsonify({'success': False, 'error': 'Sem permissão para restaurar versão'})
    
    if version.documento_id != document.id:
        return jsonify({'success': False, 'error': 'Versão não pertence ao documento'})
    
    try:
        # Calcular próxima versão
        next_version = f"{float(document.versao_atual) + 0.1:.1f}"
        
        # Criar nova versão baseada na versão restaurada
        new_version = DocumentVersion(
            documento_id=document.id,
            versao=next_version,
            conteudo=version.conteudo,
            criado_por_id=current_user.id,
            changelog=f'Restaurada versão {version.versao}'
        )
        
        # Atualizar documento
        document.versao_atual = next_version
        document.data_ultima_revisao = datetime.utcnow()
        if document.status == 'aprovado':
            document.status = 'rascunho'  # Volta para rascunho quando restaura
        
        db.session.add(new_version)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Versão {version.versao} restaurada como v{next_version}'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})