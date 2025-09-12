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

    # Inicializar extensões com a aplicação
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Criar pasta de uploads se não existir
    upload_folder = os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)

    # Registrar blueprints
    from app.routes import auth, dashboard, documents, users, approvals, audits, nonconformities, reports, equipments
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(dashboard.bp, url_prefix='/')
    app.register_blueprint(documents.bp, url_prefix='/documents')
    app.register_blueprint(users.bp, url_prefix='/users')
    app.register_blueprint(approvals.bp, url_prefix='/approvals')
    app.register_blueprint(audits.bp, url_prefix='/audits')
    app.register_blueprint(nonconformities.bp, url_prefix='/nonconformities')
    app.register_blueprint(reports.bp, url_prefix='/reports')
    app.register_blueprint(equipments.bp, url_prefix='/equipments')

    # Tratamento de erro de banco de dados
    @app.errorhandler(Exception)
    def handle_db_error(error):
        """Trata erros de conexão com banco de dados"""
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
        return str(error), 500

    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()

        # Criar usuário administrador padrão se não existir (apenas em desenvolvimento)
        from app.models import User
        if app.config.get('ENV') != 'production':
            admin = User.query.filter_by(email='admin@alphagestao.com').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@alphagestao.com',
                    nome_completo='Administrador do Sistema',
                    perfil='administrador',
                    ativo=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))