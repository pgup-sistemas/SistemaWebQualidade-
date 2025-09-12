"""
Modelos de dados para o Sistema Alpha Gestão Documental
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

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
    
    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    """Modelo de documento"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # procedimento, instrucao, politica, etc
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

class AuditLog(db.Model):
    """Modelo de log de auditoria"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    entidade_tipo = db.Column(db.String(50), nullable=False)  # document, user, etc
    entidade_id = db.Column(db.Integer, nullable=False)
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    data_acao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.acao} by user {self.usuario_id}>'