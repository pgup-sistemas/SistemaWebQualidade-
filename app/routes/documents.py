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
        
        flash('Documento criado com sucesso!', 'success')
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