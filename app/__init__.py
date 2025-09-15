"""
Alpha Gestão Documental - Sistema de Gestão de Documentos
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize logging
    Config.init_logging(app)

    # Inicializar extensões com a aplicação
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Add security headers for production
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        is_production = (os.environ.get('FLASK_ENV') == 'production' or 
                        os.environ.get('ENV') == 'production')
        
        if is_production:
            # Security headers for production
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            # Remove server header
            if 'Server' in response.headers:
                response.headers.pop('Server')
        
        return response

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Context processor para contadores de notificações
    @app.context_processor
    def inject_notification_counts():
        from app.utils.notification_counters import get_all_notification_counts
        return {'notification_counts': get_all_notification_counts()}

    # Criar pasta de uploads se não existir
    upload_folder = os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)

    # Registrar blueprints
    from app.routes import auth, dashboard, documents, document_types, users, approvals, audits, nonconformities, reports, equipments, equipment_types, groups, docs
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(dashboard.bp, url_prefix='/')
    app.register_blueprint(documents.bp, url_prefix='/documents')
    app.register_blueprint(document_types.bp)
    app.register_blueprint(users.bp, url_prefix='/users')
    app.register_blueprint(groups.bp, url_prefix='/groups')
    app.register_blueprint(approvals.bp, url_prefix='/approvals')
    app.register_blueprint(audits.bp, url_prefix='/audits')
    app.register_blueprint(nonconformities.bp, url_prefix='/nonconformities')
    app.register_blueprint(reports.bp, url_prefix='/reports')
    app.register_blueprint(equipments.bp, url_prefix='/equipments')
    app.register_blueprint(equipment_types.bp, url_prefix='/equipment_types')
    app.register_blueprint(docs.bp, url_prefix='/docs')_types.bp)

    # Tratamento de erro de banco de dados
    @app.errorhandler(Exception)
    def handle_db_error(error):
        """Trata erros de conexão com banco de dados"""
        # Log the full error for debugging
        app.logger.error(f"Application error: {error}", exc_info=True)
        
        # Handle database connection errors
        if any(err_text in str(error) for err_text in [
            'SSL connection has been closed',
            'psycopg2.OperationalError',
            'connection closed',
            'server closed the connection'
        ]):
            app.logger.error(f"Erro de conexão com banco: {error}")
            try:
                db.session.rollback()
                db.session.close()
                db.engine.dispose()
            except:
                pass
        
        # Return safe error messages based on environment
        is_production = (os.environ.get('FLASK_ENV') == 'production' or 
                        os.environ.get('ENV') == 'production')
        
        if is_production:
            # Don't expose error details in production
            return "Erro interno do servidor. Entre em contato com o suporte.", 500
        else:
            # Show full error in development
            return str(error), 500

    # Criar tabelas do banco de dados
    with app.app_context():
        try:
            db.create_all()

            # Criar usuário administrador padrão se não existir (apenas em desenvolvimento)
            from app.models import User
            is_development = (os.environ.get('CREATE_DEFAULT_ADMIN', 'False').lower() in ['true', '1', 'yes'] or
                             (app.config.get('ENV') != 'production' and 
                              os.environ.get('FLASK_ENV') != 'production'))
                              
            if is_development:
                try:
                    admin = User.query.filter_by(email='admin@alphagestao.com').first()
                    if not admin:
                        # Use environment variable for admin password or default for dev
                        admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
                        
                        admin = User()
                        admin.username = 'admin'
                        admin.email = 'admin@alphagestao.com'
                        admin.nome_completo = 'Administrador do Sistema'
                        admin.perfil = 'administrador'
                        admin.ativo = True
                        admin.set_password(admin_password)
                        db.session.add(admin)
                        db.session.commit()
                        app.logger.info("Default admin user created for development")
                except Exception as e:
                    # Se houver erro na criação do admin (como coluna não existente), apenas logar
                    app.logger.warning(f"Could not create default admin user: {e}")
                    db.session.rollback()
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
            db.session.rollback()

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))