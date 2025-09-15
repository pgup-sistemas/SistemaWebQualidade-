
"""
Rotas para gestão de equipamentos e serviços
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Equipment, ServiceRecord, User, AuditLog, EquipmentType

bp = Blueprint('equipments', __name__, url_prefix='/equipments')

@bp.route('/')
@login_required
def index():
    """Lista de equipamentos"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    tipo = request.args.get('tipo', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Equipment.query.filter_by(ativo=True)
    
    if search:
        query = query.filter(
            db.or_(
                Equipment.codigo.contains(search),
                Equipment.nome.contains(search),
                Equipment.fabricante.contains(search)
            )
        )
    
    if tipo:
        query = query.filter_by(tipo=tipo)
        
    if status:
        query = query.filter_by(status=status)
    
    equipments = query.order_by(Equipment.codigo).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    total_equipments = Equipment.query.filter_by(ativo=True).count()
    ativos = Equipment.query.filter_by(ativo=True, status='ativo').count()
    manutencao = Equipment.query.filter_by(ativo=True, status='manutencao').count()
    calibracao = Equipment.query.filter_by(ativo=True, status='calibracao').count()
    
    # Alertas de vencimento
    data_limite = datetime.utcnow() + timedelta(days=30)
    calibracoes_vencendo = Equipment.query.filter(
        Equipment.ativo == True,
        Equipment.data_proxima_calibracao <= data_limite,
        Equipment.data_proxima_calibracao >= datetime.utcnow()
    ).count()
    
    manutencoes_vencendo = Equipment.query.filter(
        Equipment.ativo == True,
        Equipment.data_proxima_manutencao <= data_limite,
        Equipment.data_proxima_manutencao >= datetime.utcnow()
    ).count()
    
    return render_template('equipments/index.html',
                         equipments=equipments,
                         search=search,
                         tipo_filter=tipo,
                         status_filter=status,
                         total_equipments=total_equipments,
                         ativos=ativos,
                         manutencao=manutencao,
                         calibracao=calibracao,
                         calibracoes_vencendo=calibracoes_vencendo,
                         manutencoes_vencendo=manutencoes_vencendo)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo equipamento"""
    if not current_user.can_create_documents():
        flash('Acesso negado.', 'error')
        return redirect(url_for('equipments.index'))
    
    if request.method == 'POST':
        try:
            equipment = Equipment(
                codigo=request.form['codigo'].strip(),
                nome=request.form['nome'].strip(),
                tipo=request.form.get('tipo', 'geral'),  # Mantido para compatibilidade
                tipo_equipamento_id=request.form.get('tipo_equipamento_id') or None,
                fabricante=request.form.get('fabricante', '').strip(),
                modelo=request.form.get('modelo', '').strip(),
                numero_serie=request.form.get('numero_serie', '').strip(),
                localizacao=request.form.get('localizacao', '').strip(),
                responsavel_id=request.form.get('responsavel_id') or None,
                status=request.form.get('status', 'ativo'),
                observacoes=request.form.get('observacoes', '').strip(),
                criado_por_id=current_user.id
            )
            
            # Datas opcionais
            if request.form.get('data_aquisicao'):
                equipment.data_aquisicao = datetime.strptime(request.form['data_aquisicao'], '%Y-%m-%d')
            
            if request.form.get('data_proxima_calibracao'):
                equipment.data_proxima_calibracao = datetime.strptime(request.form['data_proxima_calibracao'], '%Y-%m-%d')
            
            if request.form.get('data_proxima_manutencao'):
                equipment.data_proxima_manutencao = datetime.strptime(request.form['data_proxima_manutencao'], '%Y-%m-%d')
            
            if request.form.get('frequencia_calibracao'):
                equipment.frequencia_calibracao = int(request.form['frequencia_calibracao'])
            
            if request.form.get('frequencia_manutencao'):
                equipment.frequencia_manutencao = int(request.form['frequencia_manutencao'])
            
            db.session.add(equipment)
            db.session.commit()
            
            # Log de auditoria
            audit_log = AuditLog(
                usuario_id=current_user.id,
                acao='CRIAR_EQUIPAMENTO',
                entidade_tipo='equipment',
                entidade_id=equipment.id,
                detalhes=f'Equipamento criado: {equipment.codigo} - {equipment.nome}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Equipamento criado com sucesso!', 'success')
            return redirect(url_for('equipments.view', id=equipment.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar equipamento: {str(e)}', 'error')
    
    usuarios = User.query.filter_by(ativo=True).order_by(User.nome_completo).all()
    tipos_equipamento = EquipmentType.query.filter_by(ativo=True).order_by(EquipmentType.nome).all()
    return render_template('equipments/create.html', usuarios=usuarios, tipos_equipamento=tipos_equipamento)

@bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar equipamento"""
    equipment = Equipment.query.get_or_404(id)
    
    # Histórico de serviços
    services = ServiceRecord.query.filter_by(equipamento_id=id).order_by(
        ServiceRecord.data_servico.desc()
    ).all()
    
    return render_template('equipments/view.html', equipment=equipment, services=services)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar equipamento"""
    equipment = Equipment.query.get_or_404(id)
    
    if not current_user.can_admin() and equipment.criado_por_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('equipments.view', id=id))
    
    if request.method == 'POST':
        try:
            equipment.codigo = request.form['codigo'].strip()
            equipment.nome = request.form['nome'].strip()
            equipment.tipo = request.form.get('tipo', 'geral')  # Mantido para compatibilidade
            equipment.tipo_equipamento_id = request.form.get('tipo_equipamento_id') or None
            equipment.fabricante = request.form.get('fabricante', '').strip()
            equipment.modelo = request.form.get('modelo', '').strip()
            equipment.numero_serie = request.form.get('numero_serie', '').strip()
            equipment.localizacao = request.form.get('localizacao', '').strip()
            equipment.responsavel_id = request.form.get('responsavel_id') or None
            equipment.status = request.form.get('status', 'ativo')
            equipment.observacoes = request.form.get('observacoes', '').strip()
            
            # Datas opcionais
            if request.form.get('data_aquisicao'):
                equipment.data_aquisicao = datetime.strptime(request.form['data_aquisicao'], '%Y-%m-%d')
            else:
                equipment.data_aquisicao = None
            
            if request.form.get('data_proxima_calibracao'):
                equipment.data_proxima_calibracao = datetime.strptime(request.form['data_proxima_calibracao'], '%Y-%m-%d')
            else:
                equipment.data_proxima_calibracao = None
            
            if request.form.get('data_proxima_manutencao'):
                equipment.data_proxima_manutencao = datetime.strptime(request.form['data_proxima_manutencao'], '%Y-%m-%d')
            else:
                equipment.data_proxima_manutencao = None
            
            if request.form.get('frequencia_calibracao'):
                equipment.frequencia_calibracao = int(request.form['frequencia_calibracao'])
            else:
                equipment.frequencia_calibracao = None
            
            if request.form.get('frequencia_manutencao'):
                equipment.frequencia_manutencao = int(request.form['frequencia_manutencao'])
            else:
                equipment.frequencia_manutencao = None
            
            db.session.commit()
            
            # Log de auditoria
            audit_log = AuditLog(
                usuario_id=current_user.id,
                acao='EDITAR_EQUIPAMENTO',
                entidade_tipo='equipment',
                entidade_id=equipment.id,
                detalhes=f'Equipamento editado: {equipment.codigo} - {equipment.nome}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Equipamento atualizado com sucesso!', 'success')
            return redirect(url_for('equipments.view', id=equipment.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar equipamento: {str(e)}', 'error')
    
    usuarios = User.query.filter_by(ativo=True).order_by(User.nome_completo).all()
    tipos_equipamento = EquipmentType.query.filter_by(ativo=True).order_by(EquipmentType.nome).all()
    return render_template('equipments/edit.html', equipment=equipment, usuarios=usuarios, tipos_equipamento=tipos_equipamento)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Excluir equipamento"""
    equipment = Equipment.query.get_or_404(id)
    
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('equipments.view', id=id))
    
    try:
        equipment.ativo = False
        db.session.commit()
        
        # Log de auditoria
        audit_log = AuditLog(
            usuario_id=current_user.id,
            acao='EXCLUIR_EQUIPAMENTO',
            entidade_tipo='equipment',
            entidade_id=equipment.id,
            detalhes=f'Equipamento excluído: {equipment.codigo} - {equipment.nome}',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Equipamento excluído com sucesso!', 'success')
        return redirect(url_for('equipments.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir equipamento: {str(e)}', 'error')
        return redirect(url_for('equipments.view', id=id))

@bp.route('/<int:id>/services/create', methods=['GET', 'POST'])
@login_required
def create_service(id):
    """Criar registro de serviço"""
    equipment = Equipment.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            service = ServiceRecord(
                equipamento_id=id,
                tipo_servico=request.form['tipo_servico'],
                data_servico=datetime.strptime(request.form['data_servico'], '%Y-%m-%d'),
                prestador_servico=request.form.get('prestador_servico', '').strip(),
                descricao=request.form['descricao'].strip(),
                observacoes=request.form.get('observacoes', '').strip(),
                status=request.form.get('status', 'concluido'),
                responsavel_id=request.form.get('responsavel_id') or None,
                criado_por_id=current_user.id
            )
            
            if request.form.get('custo'):
                service.custo = float(request.form['custo'])
            
            if request.form.get('proximo_servico'):
                service.proximo_servico = datetime.strptime(request.form['proximo_servico'], '%Y-%m-%d')
            
            db.session.add(service)
            
            # Atualizar próximas datas no equipamento se aplicável
            if service.tipo_servico == 'calibracao' and service.proximo_servico:
                equipment.data_proxima_calibracao = service.proximo_servico
            elif service.tipo_servico == 'manutencao' and service.proximo_servico:
                equipment.data_proxima_manutencao = service.proximo_servico
            
            db.session.commit()
            
            # Log de auditoria
            audit_log = AuditLog(
                usuario_id=current_user.id,
                acao='CRIAR_SERVICO',
                entidade_tipo='service_record',
                entidade_id=service.id,
                detalhes=f'Serviço criado: {service.tipo_servico} para equipamento {equipment.codigo}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Registro de serviço criado com sucesso!', 'success')
            return redirect(url_for('equipments.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar registro de serviço: {str(e)}', 'error')
    
    usuarios = User.query.filter_by(ativo=True).order_by(User.nome_completo).all()
    return render_template('equipments/create_service.html', equipment=equipment, usuarios=usuarios)

@bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    """Editar registro de serviço"""
    service = ServiceRecord.query.get_or_404(service_id)
    equipment = service.equipamento
    
    if not current_user.can_admin() and service.criado_por_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('equipments.view', id=equipment.id))
    
    if request.method == 'POST':
        try:
            service.tipo_servico = request.form['tipo_servico']
            service.data_servico = datetime.strptime(request.form['data_servico'], '%Y-%m-%d')
            service.prestador_servico = request.form.get('prestador_servico', '').strip()
            service.descricao = request.form['descricao'].strip()
            service.observacoes = request.form.get('observacoes', '').strip()
            service.status = request.form.get('status', 'concluido')
            service.responsavel_id = request.form.get('responsavel_id') or None
            
            if request.form.get('custo'):
                service.custo = float(request.form['custo'])
            else:
                service.custo = None
            
            if request.form.get('proximo_servico'):
                service.proximo_servico = datetime.strptime(request.form['proximo_servico'], '%Y-%m-%d')
            else:
                service.proximo_servico = None
            
            db.session.commit()
            
            # Log de auditoria
            audit_log = AuditLog(
                usuario_id=current_user.id,
                acao='EDITAR_SERVICO',
                entidade_tipo='service_record',
                entidade_id=service.id,
                detalhes=f'Serviço editado: {service.tipo_servico} para equipamento {equipment.codigo}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Registro de serviço atualizado com sucesso!', 'success')
            return redirect(url_for('equipments.view', id=equipment.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar registro de serviço: {str(e)}', 'error')
    
    usuarios = User.query.filter_by(ativo=True).order_by(User.nome_completo).all()
    return render_template('equipments/edit_service.html', service=service, equipment=equipment, usuarios=usuarios)

@bp.route('/reports')
@login_required
def reports():
    """Relatórios de equipamentos"""
    if not current_user.can_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('equipments.index'))
    
    # Estatísticas gerais
    total_equipments = Equipment.query.filter_by(ativo=True).count()
    ativos = Equipment.query.filter_by(ativo=True, status='ativo').count()
    manutencao = Equipment.query.filter_by(ativo=True, status='manutencao').count()
    calibracao = Equipment.query.filter_by(ativo=True, status='calibracao').count()
    inativos = Equipment.query.filter_by(ativo=True, status='inativo').count()
    
    # Equipamentos por tipo
    tipos_stats = db.session.query(
        Equipment.tipo,
        db.func.count(Equipment.id).label('count')
    ).filter_by(ativo=True).group_by(Equipment.tipo).all()
    
    # Vencimentos próximos (30 dias)
    data_limite = datetime.utcnow() + timedelta(days=30)
    calibracoes_vencendo = Equipment.query.filter(
        Equipment.ativo == True,
        Equipment.data_proxima_calibracao <= data_limite,
        Equipment.data_proxima_calibracao >= datetime.utcnow()
    ).all()
    
    manutencoes_vencendo = Equipment.query.filter(
        Equipment.ativo == True,
        Equipment.data_proxima_manutencao <= data_limite,
        Equipment.data_proxima_manutencao >= datetime.utcnow()
    ).all()
    
    # Equipamentos vencidos
    calibracoes_vencidas = Equipment.query.filter(
        Equipment.ativo == True,
        Equipment.data_proxima_calibracao < datetime.utcnow()
    ).all()
    
    manutencoes_vencidas = Equipment.query.filter(
        Equipment.ativo == True,
        Equipment.data_proxima_manutencao < datetime.utcnow()
    ).all()
    
    # Serviços no último mês
    data_limite_mes = datetime.utcnow() - timedelta(days=30)
    servicos_mes = ServiceRecord.query.filter(
        ServiceRecord.data_servico >= data_limite_mes
    ).count()
    
    return render_template('equipments/reports.html',
                         total_equipments=total_equipments,
                         ativos=ativos,
                         manutencao=manutencao,
                         calibracao=calibracao,
                         inativos=inativos,
                         tipos_stats=tipos_stats,
                         calibracoes_vencendo=calibracoes_vencendo,
                         manutencoes_vencendo=manutencoes_vencendo,
                         calibracoes_vencidas=calibracoes_vencidas,
                         manutencoes_vencidas=manutencoes_vencidas,
                         servicos_mes=servicos_mes)
