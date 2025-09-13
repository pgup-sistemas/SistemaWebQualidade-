import os
import logging
from datetime import timedelta

class Config:
    # Configurações básicas
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    
    # Configuração do banco de dados com tratamento de reconexão
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        # Configure PostgreSQL com pooling e tratamento de reconexão
        SQLALCHEMY_DATABASE_URI = database_url
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 20,
            'max_overflow': 0,
            'connect_args': {
                'sslmode': 'prefer',
                'connect_timeout': 10,
                'application_name': 'alpha_gestao_documental'
            }
        }
    else:
        # Fallback para SQLite em desenvolvimento
        SQLALCHEMY_DATABASE_URI = 'sqlite:///alpha_gestao.db'
        SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    
    # Configurações de email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Configurações específicas do sistema
    SYSTEM_NAME = "Alpha Gestão Documental"
    COMPANY_NAME = "Sua Empresa"
    DOCUMENT_RETENTION_DAYS = 7  # Dias para manter versões antigas
    
    # Configurações de segurança
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour for CSRF token
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de logging
    @staticmethod
    def init_logging(app):
        """Initialize logging configuration"""
        is_production = (os.environ.get('FLASK_ENV') == 'production' or 
                        os.environ.get('ENV') == 'production')
        
        if is_production:
            # Production logging - more controlled
            log_level = logging.INFO
            log_format = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        else:
            # Development logging - more verbose
            log_level = logging.DEBUG
            log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s [in %(pathname)s:%(lineno)d]'
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set Flask app logger level
        app.logger.setLevel(log_level)
        
        # Reduce noise from some libraries in production
        if is_production:
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)