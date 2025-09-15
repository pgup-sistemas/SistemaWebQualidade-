"""
Modelos de dados para o Sistema Alpha Gestão Documental
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class DocumentType(db.Model):
    """Modelo de tipos de documentos dinâmicos"""
    __tablename__ = 'document_types'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    cor = db.Column(db.String(7), default='#007bff')  # Cor hexadecimal para identificação
    icone = db.Column(db.String(50), default='bi-file-text')  # Classe do ícone Bootstrap
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    criado_por = db.relationship('User', backref='tipos_documentos_criados')
    documentos = db.relationship('Document', backref='tipo_documento_obj', foreign_keys='Document.tipo_documento_id')

    def __repr__(self):
        return f'<DocumentType {self.codigo}: {self.nome}>'

class User(UserMixin, db.Model):
    """Modelo de usuário do sistema"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nome_completo = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(50), nullable=False)  # administrador, gestor_qualidade, aprovador_revisor, colaborador_leitor, auditor
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    
    # Reset de senha
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)

    # Relacionamentos
    documentos_criados = db.relationship('Document', backref='autor', lazy='dynamic', foreign_keys='Document.autor_id')
    leituras_confirmadas = db.relationship('DocumentReading', backref='usuario', lazy='dynamic')
    aprovacoes = db.relationship('ApprovalFlow', backref='responsavel', lazy='dynamic')

    def set_password(self, password):
        """Define senha com hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica senha"""
        return check_password_hash(self.password_hash, password)

    def can_create_documents(self):
        """Verifica se pode criar documentos"""
        return self.perfil in ['administrador', 'gestor_qualidade']

    def can_approve_documents(self):
        """Verifica se pode aprovar documentos"""
        return self.perfil in ['administrador', 'gestor_qualidade', 'aprovador_revisor']

    def can_admin(self):
        """Verifica se tem permissões administrativas"""
        return self.perfil == 'administrador'

    def is_admin(self):
        """Verifica se o usuário é administrador (alias para can_admin)"""
        return self.perfil == 'administrador'
    
    def generate_reset_token(self):
        """Gera token para reset de senha"""
        import secrets
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verifica se token de reset é válido"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return self.reset_token == token
    
    def clear_reset_token(self):
        """Limpa token de reset após uso"""
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    """Modelo de documento"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # procedimento, instrucao, politica, etc (mantido para compatibilidade)
    tipo_documento_id = db.Column(db.Integer, db.ForeignKey('document_types.id'))  # Novo campo para tipos dinâmicos
    status = db.Column(db.String(50), default='rascunho')  # rascunho, em_revisao, aprovado, obsoleto
    versao_atual = db.Column(db.String(10), default='1.0')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_validade = db.Column(db.DateTime)
    data_ultima_revisao = db.Column(db.DateTime)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    departamento = db.Column(db.String(100))
    palavras_chave = db.Column(db.Text)
    resumo = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos
    versoes = db.relationship('DocumentVersion', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    leituras = db.relationship('DocumentReading', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    fluxos_aprovacao = db.relationship('ApprovalFlow', backref='documento', lazy='dynamic', cascade='all, delete-orphan')

    def get_current_version(self):
        """Retorna a versão atual do documento"""
        return self.versoes.filter_by(versao=self.versao_atual).first()

    def is_expired(self):
        """Verifica se o documento está vencido"""
        if self.data_validade:
            return datetime.utcnow() > self.data_validade
        return False

    def days_to_expire(self):
        """Retorna quantos dias faltam para vencer"""
        if self.data_validade:
            delta = self.data_validade - datetime.utcnow()
            return delta.days
        return None

    def __repr__(self):
        return f'<Document {self.codigo}: {self.titulo}>'

class DocumentVersion(db.Model):
    """Modelo de versão de documento"""
    __tablename__ = 'document_versions'

    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    versao = db.Column(db.String(10), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    changelog = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    arquivo_path = db.Column(db.String(255))  # Para arquivos PDF gerados

    # Relacionamento
    criado_por = db.relationship('User', backref='versoes_criadas')

    def __repr__(self):
        return f'<DocumentVersion {self.versao} of {self.documento_id}>'

class ApprovalFlow(db.Model):
    """Modelo de fluxo de aprovação"""
    __tablename__ = 'approval_flows'

    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    etapa = db.Column(db.String(50), nullable=False)  # revisao, aprovacao
    status = db.Column(db.String(50), default='pendente')  # pendente, aprovado, rejeitado
    ordem = db.Column(db.Integer, default=1)
    data_atribuicao = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime)
    comentarios = db.Column(db.Text)
    prazo = db.Column(db.DateTime)

    def is_overdue(self):
        """Verifica se está atrasado"""
        if self.prazo and self.status == 'pendente':
            return datetime.utcnow() > self.prazo
        return False

    def __repr__(self):
        return f'<ApprovalFlow {self.etapa} for doc {self.documento_id}>'

class DocumentReading(db.Model):
    """Modelo de confirmação de leitura"""
    __tablename__ = 'document_readings'

    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    versao_lida = db.Column(db.String(10), nullable=False)
    data_leitura = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    def __repr__(self):
        return f'<DocumentReading user {self.usuario_id} read doc {self.documento_id}>'


class NonConformity(db.Model):
    """Modelo de não conformidade (CAPA)"""
    __tablename__ = 'non_conformities'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # interna, externa, auditoria, cliente
    criticidade = db.Column(db.String(20), nullable=False)  # baixa, media, alta, critica
    status = db.Column(db.String(50), default='aberta')  # aberta, em_analise, em_tratamento, fechada
    origem = db.Column(db.String(100))  # auditoria, cliente, processo, etc
    area_responsavel = db.Column(db.String(100))
    data_abertura = db.Column(db.DateTime, default=datetime.utcnow)
    data_prazo = db.Column(db.DateTime)
    data_fechamento = db.Column(db.DateTime)

    # Relacionamentos
    aberto_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    documento_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    aberto_por = db.relationship('User', foreign_keys=[aberto_por_id], backref='ncs_abertas')
    responsavel = db.relationship('User', foreign_keys=[responsavel_id], backref='ncs_responsavel')
    documento = db.relationship('Document', backref='nao_conformidades')

    # Relacionamentos com ações CAPA
    acoes_corretivas = db.relationship('CorrectiveAction', backref='nao_conformidade', lazy='dynamic', cascade='all, delete-orphan')

    def is_overdue(self):
        """Verifica se está atrasada"""
        if self.data_prazo and self.status != 'fechada':
            return datetime.utcnow() > self.data_prazo
        return False

    def days_to_deadline(self):
        """Dias para o prazo"""
        if self.data_prazo and self.status != 'fechada':
            delta = self.data_prazo - datetime.utcnow()
            return delta.days
        return None

    def __repr__(self):
        return f'<NonConformity {self.codigo}: {self.titulo}>'

class CorrectiveAction(db.Model):
    """Modelo de ação corretiva/preventiva (CAPA)"""
    __tablename__ = 'corrective_actions'

    id = db.Column(db.Integer, primary_key=True)
    nao_conformidade_id = db.Column(db.Integer, db.ForeignKey('non_conformities.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # corretiva, preventiva
    descricao = db.Column(db.Text, nullable=False)
    justificativa = db.Column(db.Text)
    status = db.Column(db.String(50), default='pendente')  # pendente, em_andamento, concluida, cancelada
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_prazo = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)

    # Relacionamentos
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    responsavel = db.relationship('User', foreign_keys=[responsavel_id], backref='acoes_responsavel')
    criado_por = db.relationship('User', foreign_keys=[criado_por_id], backref='acoes_criadas')

    def is_overdue(self):
        """Verifica se está atrasada"""
        if self.data_prazo and self.status not in ['concluida', 'cancelada']:
            return datetime.utcnow() > self.data_prazo
        return False

    def __repr__(self):
        return f'<CorrectiveAction {self.tipo} for NC {self.nao_conformidade_id}>'

class Audit(db.Model):
    """Modelo de auditoria interna"""
    __tablename__ = 'audits'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # interna, externa, certificacao
    escopo = db.Column(db.Text, nullable=False)
    objetivos = db.Column(db.Text)
    area_auditada = db.Column(db.String(100))
    status = db.Column(db.String(50), default='planejada')  # planejada, em_andamento, concluida, cancelada
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_inicio = db.Column(db.DateTime)
    data_fim = db.Column(db.DateTime)
    data_relatorio = db.Column(db.DateTime)

    # Relacionamentos
    auditor_lider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    auditor_lider = db.relationship('User', foreign_keys=[auditor_lider_id], backref='auditorias_lideradas')
    criado_por = db.relationship('User', foreign_keys=[criado_por_id], backref='auditorias_criadas')

    # Relacionamentos com checklists e achados
    checklists = db.relationship('AuditChecklist', backref='auditoria', lazy='dynamic', cascade='all, delete-orphan')
    achados = db.relationship('AuditFinding', backref='auditoria', lazy='dynamic', cascade='all, delete-orphan')

    def get_conformidade_percentage(self):
        """Calcula percentual de conformidade"""
        total_items = self.checklists.count()
        if total_items == 0:
            return 0

        conforme_items = self.checklists.filter_by(status='conforme').count()
        return round((conforme_items / total_items) * 100, 1)

    def __repr__(self):
        return f'<Audit {self.codigo}: {self.titulo}>'

class AuditChecklist(db.Model):
    """Modelo de checklist de auditoria"""
    __tablename__ = 'audit_checklists'

    id = db.Column(db.Integer, primary_key=True)
    auditoria_id = db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=False)
    item = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    requisito = db.Column(db.String(100))  # ISO 9001, etc
    status = db.Column(db.String(20), default='pendente')  # pendente, conforme, nao_conforme, nao_aplicavel
    observacoes = db.Column(db.Text)
    evidencias = db.Column(db.Text)
    data_verificacao = db.Column(db.DateTime)

    # Relacionamento
    verificado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    verificado_por = db.relationship('User', backref='verificacoes_auditoria')

    def __repr__(self):
        return f'<AuditChecklist {self.item} - {self.status}>'

class AuditFinding(db.Model):
    """Modelo de achado de auditoria"""
    __tablename__ = 'audit_findings'

    id = db.Column(db.Integer, primary_key=True)
    auditoria_id = db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # nao_conformidade, observacao, oportunidade_melhoria
    descricao = db.Column(db.Text, nullable=False)
    criterio = db.Column(db.Text)  # critério de auditoria
    evidencia = db.Column(db.Text)
    criticidade = db.Column(db.String(20), default='media')  # baixa, media, alta
    status = db.Column(db.String(50), default='aberto')  # aberto, em_tratamento, fechado
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    identificado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    identificado_por = db.relationship('User', foreign_keys=[identificado_por_id], backref='achados_identificados')
    responsavel = db.relationship('User', foreign_keys=[responsavel_id], backref='achados_responsavel')

    def __repr__(self):
        return f'<AuditFinding {self.tipo} in audit {self.auditoria_id}>'

class DocumentSignature(db.Model):
    """Modelo de assinatura digital de documentos"""
    __tablename__ = 'document_signatures'

    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    versao_documento = db.Column(db.String(10), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo_assinatura = db.Column(db.String(20), nullable=False)  # digital, eletronica, manuscrita
    hash_documento = db.Column(db.String(256))  # Hash do documento assinado
    certificado_info = db.Column(db.Text)  # Informações do certificado digital
    ip_address = db.Column(db.String(45))
    data_assinatura = db.Column(db.DateTime, default=datetime.utcnow)
    valida = db.Column(db.Boolean, default=True)

    # Relacionamentos
    documento = db.relationship('Document', backref='assinaturas')
    usuario = db.relationship('User', backref='assinaturas_realizadas')

    def __repr__(self):
        return f'<DocumentSignature {self.tipo_assinatura} by user {self.usuario_id}>'

class Equipment(db.Model):
    """Modelo de equipamentos"""
    __tablename__ = 'equipments'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # medicao, teste, producao, seguranca, etc
    fabricante = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    localizacao = db.Column(db.String(100))
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(30), default='ativo')  # ativo, inativo, manutencao, calibracao
    data_aquisicao = db.Column(db.DateTime)
    data_proxima_calibracao = db.Column(db.DateTime)
    data_proxima_manutencao = db.Column(db.DateTime)
    frequencia_calibracao = db.Column(db.Integer)  # em meses
    frequencia_manutencao = db.Column(db.Integer)  # em meses
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    responsavel = db.relationship('User', foreign_keys=[responsavel_id], backref='equipamentos_responsavel')
    criado_por = db.relationship('User', foreign_keys=[criado_por_id], backref='equipamentos_criados')
    registros_servico = db.relationship('ServiceRecord', backref='equipamento', lazy='dynamic', cascade='all, delete-orphan')

    def is_calibration_due(self):
        """Verifica se calibração está vencida"""
        if self.data_proxima_calibracao:
            return datetime.utcnow() > self.data_proxima_calibracao
        return False

    def is_maintenance_due(self):
        """Verifica se manutenção está vencida"""
        if self.data_proxima_manutencao:
            return datetime.utcnow() > self.data_proxima_manutencao
        return False

    def days_to_calibration(self):
        """Dias para próxima calibração"""
        if self.data_proxima_calibracao:
            delta = self.data_proxima_calibracao - datetime.utcnow()
            return delta.days
        return None

    def days_to_maintenance(self):
        """Dias para próxima manutenção"""
        if self.data_proxima_manutencao:
            delta = self.data_proxima_manutencao - datetime.utcnow()
            return delta.days
        return None

    def __repr__(self):
        return f'<Equipment {self.codigo}: {self.nome}>'

class ServiceRecord(db.Model):
    """Modelo de registro de serviços (manutenção, calibração, etc)"""
    __tablename__ = 'service_records'

    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)
    tipo_servico = db.Column(db.String(50), nullable=False)  # manutencao, calibracao, reparo, inspecao
    data_servico = db.Column(db.DateTime, nullable=False)
    prestador_servico = db.Column(db.String(200))  # empresa ou pessoa responsável
    descricao = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(30), default='concluido')  # agendado, em_andamento, concluido, cancelado
    custo = db.Column(db.Numeric(10, 2))
    proximo_servico = db.Column(db.DateTime)  # quando deve ser o próximo serviço
    certificado_path = db.Column(db.String(255))  # caminho para certificado de calibração
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relacionamentos
    criado_por = db.relationship('User', foreign_keys=[criado_por_id], backref='servicos_criados')
    responsavel = db.relationship('User', foreign_keys=[responsavel_id], backref='servicos_responsavel')

    def is_overdue(self):
        """Verifica se o próximo serviço está atrasado"""
        if self.proximo_servico and self.status == 'concluido':
            return datetime.utcnow() > self.proximo_servico
        return False

    def __repr__(self):
        return f'<ServiceRecord {self.tipo_servico} for equipment {self.equipamento_id}>'

class EmailNotification(db.Model):
    """Modelo de notificações por email"""
    __tablename__ = 'email_notifications'

    id = db.Column(db.Integer, primary_key=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # documento_vencendo, aprovacao_pendente, nc_aberta, etc
    assunto = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, enviado, erro
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_envio = db.Column(db.DateTime)
    tentativas = db.Column(db.Integer, default=0)
    erro_mensagem = db.Column(db.Text)

    # Relacionamentos
    entidade_tipo = db.Column(db.String(50))  # document, non_conformity, audit, etc
    entidade_id = db.Column(db.Integer)

    destinatario = db.relationship('User', backref='notificacoes_email')

    def __repr__(self):
        return f'<EmailNotification {self.tipo} to user {self.destinatario_id}>'

class AuditLog(db.Model):
    """Modelo de log de auditoria para rastrear ações do sistema"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    acao = db.Column(db.String(100), nullable=False)  # login, logout, create_user, update_user, etc.
    recurso = db.Column(db.String(100), nullable=True)  # user, document, etc.
    recurso_id = db.Column(db.Integer, nullable=True)
    detalhes = db.Column(db.Text, nullable=True)  # JSON com detalhes da ação
    ip_address = db.Column(db.String(45), nullable=True)  # Suporte IPv6
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='sucesso')  # sucesso, falha, erro
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamento
    usuario = db.relationship('User', backref='logs_auditoria')
    
    def __repr__(self):
        return f'<AuditLog {self.acao} by user {self.usuario_id}>'
    
    @staticmethod
    def registrar_acao(usuario_id, acao, recurso=None, recurso_id=None, 
                      detalhes=None, ip_address=None, user_agent=None, status='sucesso'):
        """
        Registra uma ação de auditoria
        """
        log = AuditLog(
            usuario_id=usuario_id,
            acao=acao,
            recurso=recurso,
            recurso_id=recurso_id,
            detalhes=detalhes,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log