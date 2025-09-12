"""
Rotas para gestão de não conformidades (CAPA) - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import NonConformity, CorrectiveAction, User, Document
from app import db
from datetime import datetime, timedelta
import uuid

bp = Blueprint('nonconformities', __name__)

@bp.route('/')
@login_required
def index():
    """Lista de não conformidades"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    criticidade = request.args.get('criticidade', '')
    search = request.args.get('search', '')
    
    query = NonConformity.query
    
    if search:
        query = query.filter(
            (NonConformity.titulo.contains(search)) |
            (NonConformity.codigo.contains(search)) |
            (NonConformity.descricao.contains(search))
        )
    
    if status:
        query = query.filter_by(status=status)
        
    if criticidade:
        query = query.filter_by(criticidade=criticidade)
    
    ncs = query.order_by(NonConformity.data_abertura.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    total_abertas = NonConformity.query.filter_by(status='aberta').count()
    total_atrasadas = NonConformity.query.filter(
        NonConformity.data_prazo < datetime.utcnow(),
        NonConformity.status != 'fechada'
    ).count()
    
    return render_template('nonconformities/index.html', 
                         ncs=ncs, 
                         search=search,
                         current_status=status,
                         current_criticidade=criticidade,
                         total_abertas=total_abertas,
                         total_atrasadas=total_atrasadas)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar nova não conformidade"""
    if not current_user.can_create_documents():
        flash('Você não tem permissão para criar não conformidades.', 'error')
        return redirect(url_for('nonconformities.index'))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')
        criticidade = request.form.get('criticidade')
        origem = request.form.get('origem')
        area_responsavel = request.form.get('area_responsavel')
        responsavel_id = request.form.get('responsavel_id')
        documento_id = request.form.get('documento_id') or None
        data_prazo = request.form.get('data_prazo')
        
        # Gerar código único
        ano = datetime.now().year
        count = NonConformity.query.filter(
            NonConformity.codigo.like(f'NC-{ano}-%')
        ).count() + 1
        codigo = f"NC-{ano}-{count:04d}"
        
        nc = NonConformity(
            codigo=codigo,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            criticidade=criticidade,
            origem=origem,
            area_responsavel=area_responsavel,
            aberto_por_id=current_user.id,
            responsavel_id=responsavel_id if responsavel_id else None,
            documento_id=documento_id if documento_id else None,
            data_prazo=datetime.strptime(data_prazo, '%Y-%m-%d') if data_prazo else None
        )
        
        db.session.add(nc)
        db.session.commit()
        
        flash('Não conformidade criada com sucesso!', 'success')
        return redirect(url_for('nonconformities.view', id=nc.id))
    
    # Buscar usuários para responsável
    usuarios = User.query.filter_by(ativo=True).order_by(User.nome_completo).all()
    documentos = Document.query.filter_by(ativo=True).order_by(Document.titulo).all()
    
    return render_template('nonconformities/create.html', 
                         usuarios=usuarios, 
                         documentos=documentos)

@bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar não conformidade"""
    nc = NonConformity.query.get_or_404(id)
    acoes = nc.acoes_corretivas.order_by(CorrectiveAction.data_criacao.desc()).all()
    
    return render_template('nonconformities/view.html', nc=nc, acoes=acoes)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar não conformidade"""
    nc = NonConformity.query.get_or_404(id)
    
    if not (current_user.can_admin() or nc.aberto_por_id == current_user.id):
        flash('Você não tem permissão para editar esta não conformidade.', 'error')
        return redirect(url_for('nonconformities.view', id=id))
    
    if request.method == 'POST':
        nc.titulo = request.form.get('titulo')
        nc.descricao = request.form.get('descricao')
        nc.tipo = request.form.get('tipo')
        nc.criticidade = request.form.get('criticidade')
        nc.origem = request.form.get('origem')
        nc.area_responsavel = request.form.get('area_responsavel')
        nc.status = request.form.get('status')
        
        responsavel_id = request.form.get('responsavel_id')
        nc.responsavel_id = responsavel_id if responsavel_id else None
        
        data_prazo = request.form.get('data_prazo')
        nc.data_prazo = datetime.strptime(data_prazo, '%Y-%m-%d') if data_prazo else None
        
        if nc.status == 'fechada' and not nc.data_fechamento:
            nc.data_fechamento = datetime.utcnow()
        elif nc.status != 'fechada':
            nc.data_fechamento = None
        
        db.session.commit()
        
        flash('Não conformidade atualizada com sucesso!', 'success')
        return redirect(url_for('nonconformities.view', id=id))
    
    usuarios = User.query.filter_by(ativo=True).order_by(User.nome_completo).all()
    return render_template('nonconformities/edit.html', nc=nc, usuarios=usuarios)

@bp.route('/<int:id>/actions/create', methods=['POST'])
@login_required
def create_action(id):
    """Criar ação corretiva/preventiva"""
    nc = NonConformity.query.get_or_404(id)
    
    if not current_user.can_create_documents():
        flash('Você não tem permissão para criar ações.', 'error')
        return redirect(url_for('nonconformities.view', id=id))
    
    tipo = request.form.get('tipo')
    descricao = request.form.get('descricao')
    justificativa = request.form.get('justificativa')
    responsavel_id = request.form.get('responsavel_id')
    data_prazo = request.form.get('data_prazo')
    
    acao = CorrectiveAction(
        nao_conformidade_id=nc.id,
        tipo=tipo,
        descricao=descricao,
        justificativa=justificativa,
        responsavel_id=responsavel_id,
        criado_por_id=current_user.id,
        data_prazo=datetime.strptime(data_prazo, '%Y-%m-%d') if data_prazo else None
    )
    
    db.session.add(acao)
    
    # Atualizar status da NC se necessário
    if nc.status == 'aberta':
        nc.status = 'em_tratamento'
    
    db.session.commit()
    
    flash('Ação criada com sucesso!', 'success')
    return redirect(url_for('nonconformities.view', id=id))

@bp.route('/actions/<int:action_id>/update', methods=['POST'])
@login_required
def update_action(action_id):
    """Atualizar status de ação"""
    acao = CorrectiveAction.query.get_or_404(action_id)
    
    if not (current_user.can_admin() or acao.responsavel_id == current_user.id):
        flash('Você não tem permissão para atualizar esta ação.', 'error')
        return redirect(url_for('nonconformities.view', id=acao.nao_conformidade_id))
    
    status = request.form.get('status')
    acao.status = status
    
    if status == 'concluida':
        acao.data_conclusao = datetime.utcnow()
    
    db.session.commit()
    
    flash('Status da ação atualizado!', 'success')
    return redirect(url_for('nonconformities.view', id=acao.nao_conformidade_id))

@bp.route('/reports')
@login_required
def reports():
    """Relatórios de não conformidades"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('nonconformities.index'))
    
    # Estatísticas gerais
    total_ncs = NonConformity.query.count()
    abertas = NonConformity.query.filter_by(status='aberta').count()
    em_tratamento = NonConformity.query.filter_by(status='em_tratamento').count()
    fechadas = NonConformity.query.filter_by(status='fechada').count()
    
    # NCs por criticidade
    criticas = NonConformity.query.filter_by(criticidade='critica').count()
    altas = NonConformity.query.filter_by(criticidade='alta').count()
    medias = NonConformity.query.filter_by(criticidade='media').count()
    baixas = NonConformity.query.filter_by(criticidade='baixa').count()
    
    # NCs atrasadas
    atrasadas = NonConformity.query.filter(
        NonConformity.data_prazo < datetime.utcnow(),
        NonConformity.status != 'fechada'
    ).count()
    
    return render_template('nonconformities/reports.html',
                         total_ncs=total_ncs,
                         abertas=abertas,
                         em_tratamento=em_tratamento,
                         fechadas=fechadas,
                         criticas=criticas,
                         altas=altas,
                         medias=medias,
                         baixas=baixas,
                         atrasadas=atrasadas)