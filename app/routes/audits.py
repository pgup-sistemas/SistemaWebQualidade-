"""
Rotas para módulo de auditorias internas - Sistema Alpha Gestão Documental
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import Audit, AuditChecklist, AuditFinding, User
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import uuid

bp = Blueprint('audits', __name__)

@bp.route('/')
@login_required
def index():
    """Lista de auditorias"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    tipo = request.args.get('tipo', '')
    search = request.args.get('search', '')
    
    query = Audit.query
    
    if search:
        query = query.filter(
            (Audit.titulo.contains(search)) |
            (Audit.codigo.contains(search)) |
            (Audit.escopo.contains(search))
        )
    
    if status:
        query = query.filter_by(status=status)
        
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    auditorias = query.order_by(Audit.data_criacao.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    total_planejadas = Audit.query.filter_by(status='planejada').count()
    total_andamento = Audit.query.filter_by(status='em_andamento').count()
    total_concluidas = Audit.query.filter_by(status='concluida').count()
    
    return render_template('audits/index.html', 
                         auditorias=auditorias, 
                         search=search,
                         current_status=status,
                         current_tipo=tipo,
                         total_planejadas=total_planejadas,
                         total_andamento=total_andamento,
                         total_concluidas=total_concluidas)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar nova auditoria"""
    if not current_user.can_admin():
        flash('Você não tem permissão para criar auditorias.', 'error')
        return redirect(url_for('audits.index'))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        tipo = request.form.get('tipo')
        escopo = request.form.get('escopo')
        objetivos = request.form.get('objetivos')
        area_auditada = request.form.get('area_auditada')
        auditor_lider_id = request.form.get('auditor_lider_id')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        
        # Gerar código único
        ano = datetime.now().year
        count = Audit.query.filter(
            Audit.codigo.like(f'AUD-{ano}-%')
        ).count() + 1
        codigo = f"AUD-{ano}-{count:04d}"
        
        auditoria = Audit(
            codigo=codigo,
            titulo=titulo,
            tipo=tipo,
            escopo=escopo,
            objetivos=objetivos,
            area_auditada=area_auditada,
            auditor_lider_id=auditor_lider_id,
            criado_por_id=current_user.id,
            data_inicio=datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None,
            data_fim=datetime.strptime(data_fim, '%Y-%m-%d') if data_fim else None
        )
        
        db.session.add(auditoria)
        db.session.commit()
        
        flash('Auditoria criada com sucesso!', 'success')
        return redirect(url_for('audits.view', id=auditoria.id))
    
    # Buscar usuários que podem ser auditores
    auditores = User.query.filter(
        User.ativo == True,
        User.perfil.in_(['administrador', 'gestor_qualidade', 'auditor'])
    ).order_by(User.nome_completo).all()
    
    return render_template('audits/create.html', auditores=auditores)

@bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar auditoria"""
    auditoria = Audit.query.get_or_404(id)
    checklists = auditoria.checklists.order_by(AuditChecklist.id).all()
    achados = auditoria.achados.order_by(AuditFinding.data_criacao.desc()).all()
    
    # Estatísticas da auditoria
    total_items = len(checklists)
    conforme = len([c for c in checklists if c.status == 'conforme'])
    nao_conforme = len([c for c in checklists if c.status == 'nao_conforme'])
    nao_aplicavel = len([c for c in checklists if c.status == 'nao_aplicavel'])
    pendente = len([c for c in checklists if c.status == 'pendente'])
    
    percentual_conformidade = auditoria.get_conformidade_percentage()
    
    return render_template('audits/view.html', 
                         auditoria=auditoria, 
                         checklists=checklists,
                         achados=achados,
                         total_items=total_items,
                         conforme=conforme,
                         nao_conforme=nao_conforme,
                         nao_aplicavel=nao_aplicavel,
                         pendente=pendente,
                         percentual_conformidade=percentual_conformidade)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar auditoria"""
    auditoria = Audit.query.get_or_404(id)
    
    if not (current_user.can_admin() or auditoria.criado_por_id == current_user.id):
        flash('Você não tem permissão para editar esta auditoria.', 'error')
        return redirect(url_for('audits.view', id=id))
    
    if request.method == 'POST':
        auditoria.titulo = request.form.get('titulo')
        auditoria.tipo = request.form.get('tipo')
        auditoria.escopo = request.form.get('escopo')
        auditoria.objetivos = request.form.get('objetivos')
        auditoria.area_auditada = request.form.get('area_auditada')
        auditoria.status = request.form.get('status')
        auditoria.auditor_lider_id = request.form.get('auditor_lider_id')
        
        data_inicio = request.form.get('data_inicio')
        auditoria.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None
        
        data_fim = request.form.get('data_fim')
        auditoria.data_fim = datetime.strptime(data_fim, '%Y-%m-%d') if data_fim else None
        
        if auditoria.status == 'concluida' and not auditoria.data_relatorio:
            auditoria.data_relatorio = datetime.utcnow()
        
        db.session.commit()
        
        flash('Auditoria atualizada com sucesso!', 'success')
        return redirect(url_for('audits.view', id=id))
    
    auditores = User.query.filter(
        User.ativo == True,
        User.perfil.in_(['administrador', 'gestor_qualidade', 'auditor'])
    ).order_by(User.nome_completo).all()
    
    return render_template('audits/edit.html', auditoria=auditoria, auditores=auditores)

@bp.route('/<int:id>/checklist/add', methods=['POST'])
@login_required
def add_checklist_item(id):
    """Adicionar item ao checklist"""
    auditoria = Audit.query.get_or_404(id)
    
    if not (current_user.can_admin() or auditoria.auditor_lider_id == current_user.id):
        flash('Você não tem permissão para editar esta auditoria.', 'error')
        return redirect(url_for('audits.view', id=id))
    
    item = request.form.get('item')
    descricao = request.form.get('descricao')
    requisito = request.form.get('requisito')
    
    checklist_item = AuditChecklist(
        auditoria_id=auditoria.id,
        item=item,
        descricao=descricao,
        requisito=requisito
    )
    
    db.session.add(checklist_item)
    db.session.commit()
    
    flash('Item adicionado ao checklist!', 'success')
    return redirect(url_for('audits.view', id=id))

@bp.route('/checklist/<int:item_id>/update', methods=['POST'])
@login_required
def update_checklist_item(item_id):
    """Atualizar item do checklist"""
    item = AuditChecklist.query.get_or_404(item_id)
    auditoria = item.auditoria
    
    if not (current_user.can_admin() or auditoria.auditor_lider_id == current_user.id):
        flash('Você não tem permissão para atualizar este item.', 'error')
        return redirect(url_for('audits.view', id=auditoria.id))
    
    item.status = request.form.get('status')
    item.observacoes = request.form.get('observacoes')
    item.evidencias = request.form.get('evidencias')
    item.verificado_por_id = current_user.id
    item.data_verificacao = datetime.utcnow()
    
    db.session.commit()
    
    flash('Item do checklist atualizado!', 'success')
    return redirect(url_for('audits.view', id=auditoria.id))

@bp.route('/<int:id>/findings/add', methods=['POST'])
@login_required
def add_finding(id):
    """Adicionar achado de auditoria"""
    auditoria = Audit.query.get_or_404(id)
    
    if not (current_user.can_admin() or auditoria.auditor_lider_id == current_user.id):
        flash('Você não tem permissão para adicionar achados.', 'error')
        return redirect(url_for('audits.view', id=id))
    
    tipo = request.form.get('tipo')
    descricao = request.form.get('descricao')
    criterio = request.form.get('criterio')
    evidencia = request.form.get('evidencia')
    criticidade = request.form.get('criticidade')
    responsavel_id = request.form.get('responsavel_id')
    
    achado = AuditFinding(
        auditoria_id=auditoria.id,
        tipo=tipo,
        descricao=descricao,
        criterio=criterio,
        evidencia=evidencia,
        criticidade=criticidade,
        identificado_por_id=current_user.id,
        responsavel_id=responsavel_id if responsavel_id else None
    )
    
    db.session.add(achado)
    db.session.commit()
    
    flash('Achado registrado com sucesso!', 'success')
    return redirect(url_for('audits.view', id=id))

@bp.route('/findings/<int:finding_id>/update', methods=['POST'])
@login_required
def update_finding(finding_id):
    """Atualizar status de achado"""
    achado = AuditFinding.query.get_or_404(finding_id)
    
    if not (current_user.can_admin() or achado.responsavel_id == current_user.id):
        flash('Você não tem permissão para atualizar este achado.', 'error')
        return redirect(url_for('audits.view', id=achado.auditoria_id))
    
    status = request.form.get('status')
    achado.status = status
    
    db.session.commit()
    
    flash('Status do achado atualizado!', 'success')
    return redirect(url_for('audits.view', id=achado.auditoria_id))

@bp.route('/reports')
@login_required
def reports():
    """Relatórios de auditorias"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('audits.index'))
    
    # Estatísticas gerais
    total_auditorias = Audit.query.count()
    planejadas = Audit.query.filter_by(status='planejada').count()
    em_andamento = Audit.query.filter_by(status='em_andamento').count()
    concluidas = Audit.query.filter_by(status='concluida').count()
    
    # Auditorias por tipo
    internas = Audit.query.filter_by(tipo='interna').count()
    externas = Audit.query.filter_by(tipo='externa').count()
    certificacao = Audit.query.filter_by(tipo='certificacao').count()
    
    # Percentual médio de conformidade
    auditorias_concluidas = Audit.query.filter_by(status='concluida').all()
    conformidade_media = 0
    if auditorias_concluidas:
        total_conformidade = sum([a.get_conformidade_percentage() for a in auditorias_concluidas])
        conformidade_media = round(total_conformidade / len(auditorias_concluidas), 1)
    
    return render_template('audits/reports.html',
                         total_auditorias=total_auditorias,
                         planejadas=planejadas,
                         em_andamento=em_andamento,
                         concluidas=concluidas,
                         internas=internas,
                         externas=externas,
                         certificacao=certificacao,
                         conformidade_media=conformidade_media)