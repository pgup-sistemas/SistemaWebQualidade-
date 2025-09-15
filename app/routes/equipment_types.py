
"""
Rotas para gestão de tipos de equipamentos
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import EquipmentType, AuditLog

bp = Blueprint('equipment_types', __name__, url_prefix='/equipment_types')

@bp.route('/')
@login_required
def index():
    """Lista de tipos de equipamentos"""
    if not current_user.can_admin():
        flash('Acesso negado. Apenas administradores podem gerenciar tipos de equipamentos.', 'error')
        return redirect(url_for('equipments.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = EquipmentType.query.filter_by(ativo=True)
    
    if search:
        query = query.filter(
            db.or_(
                EquipmentType.codigo.contains(search),
                EquipmentType.nome.contains(search)
            )
        )
    
    tipos = query.order_by(EquipmentType.nome).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('equipment_types/index.html', tipos=tipos, search=search)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo tipo de equipamento"""
    if not current_user.can_admin():
        flash('Acesso negado. Apenas administradores podem criar tipos de equipamentos.', 'error')
        return redirect(url_for('equipment_types.index'))
    
    if request.method == 'POST':
        try:
            tipo = EquipmentType(
                codigo=request.form['codigo'].strip().upper(),
                nome=request.form['nome'].strip(),
                descricao=request.form.get('descricao', '').strip(),
                cor=request.form.get('cor', '#6c757d'),
                icone=request.form.get('icone', 'bi-gear'),
                requer_calibracao=bool(request.form.get('requer_calibracao')),
                requer_manutencao=bool(request.form.get('requer_manutencao')),
                criado_por_id=current_user.id
            )
            
            # Frequências padrão opcionais
            if request.form.get('frequencia_calibracao_padrao'):
                tipo.frequencia_calibracao_padrao = int(request.form['frequencia_calibracao_padrao'])
            
            if request.form.get('frequencia_manutencao_padrao'):
                tipo.frequencia_manutencao_padrao = int(request.form['frequencia_manutencao_padrao'])
            
            db.session.add(tipo)
            db.session.commit()
            
            # Log de auditoria
            audit_log = AuditLog(
                usuario_id=current_user.id,
                acao='CRIAR_TIPO_EQUIPAMENTO',
                entidade_tipo='equipment_type',
                entidade_id=tipo.id,
                detalhes=f'Tipo de equipamento criado: {tipo.codigo} - {tipo.nome}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Tipo de equipamento criado com sucesso!', 'success')
            return redirect(url_for('equipment_types.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tipo de equipamento: {str(e)}', 'error')
    
    return render_template('equipment_types/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Editar tipo de equipamento"""
    if not current_user.can_admin():
        flash('Acesso negado. Apenas administradores podem editar tipos de equipamentos.', 'error')
        return redirect(url_for('equipment_types.index'))
    
    tipo = EquipmentType.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            tipo.codigo = request.form['codigo'].strip().upper()
            tipo.nome = request.form['nome'].strip()
            tipo.descricao = request.form.get('descricao', '').strip()
            tipo.cor = request.form.get('cor', '#6c757d')
            tipo.icone = request.form.get('icone', 'bi-gear')
            tipo.requer_calibracao = bool(request.form.get('requer_calibracao'))
            tipo.requer_manutencao = bool(request.form.get('requer_manutencao'))
            
            # Frequências padrão opcionais
            if request.form.get('frequencia_calibracao_padrao'):
                tipo.frequencia_calibracao_padrao = int(request.form['frequencia_calibracao_padrao'])
            else:
                tipo.frequencia_calibracao_padrao = None
            
            if request.form.get('frequencia_manutencao_padrao'):
                tipo.frequencia_manutencao_padrao = int(request.form['frequencia_manutencao_padrao'])
            else:
                tipo.frequencia_manutencao_padrao = None
            
            db.session.commit()
            
            # Log de auditoria
            audit_log = AuditLog(
                usuario_id=current_user.id,
                acao='EDITAR_TIPO_EQUIPAMENTO',
                entidade_tipo='equipment_type',
                entidade_id=tipo.id,
                detalhes=f'Tipo de equipamento editado: {tipo.codigo} - {tipo.nome}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Tipo de equipamento atualizado com sucesso!', 'success')
            return redirect(url_for('equipment_types.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tipo de equipamento: {str(e)}', 'error')
    
    return render_template('equipment_types/edit.html', tipo=tipo)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Excluir tipo de equipamento"""
    if not current_user.can_admin():
        flash('Acesso negado. Apenas administradores podem excluir tipos de equipamentos.', 'error')
        return redirect(url_for('equipment_types.index'))
    
    tipo = EquipmentType.query.get_or_404(id)
    
    # Verificar se há equipamentos usando este tipo
    from app.models import Equipment
    equipamentos_count = Equipment.query.filter_by(tipo_equipamento_id=id, ativo=True).count()
    
    if equipamentos_count > 0:
        flash(f'Não é possível excluir este tipo. Há {equipamentos_count} equipamento(s) usando este tipo.', 'warning')
        return redirect(url_for('equipment_types.index'))
    
    try:
        tipo.ativo = False
        db.session.commit()
        
        # Log de auditoria
        audit_log = AuditLog(
            usuario_id=current_user.id,
            acao='EXCLUIR_TIPO_EQUIPAMENTO',
            entidade_tipo='equipment_type',
            entidade_id=tipo.id,
            detalhes=f'Tipo de equipamento excluído: {tipo.codigo} - {tipo.nome}',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Tipo de equipamento excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tipo de equipamento: {str(e)}', 'error')
    
    return redirect(url_for('equipment_types.index'))

@bp.route('/api/get_defaults/<int:id>')
@login_required
def get_defaults(id):
    """API para obter configurações padrão de um tipo de equipamento"""
    tipo = EquipmentType.query.get_or_404(id)
    
    return jsonify({
        'requer_calibracao': tipo.requer_calibracao,
        'frequencia_calibracao_padrao': tipo.frequencia_calibracao_padrao,
        'requer_manutencao': tipo.requer_manutencao,
        'frequencia_manutencao_padrao': tipo.frequencia_manutencao_padrao
    })
