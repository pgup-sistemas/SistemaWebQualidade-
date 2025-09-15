# Pacote de rotas do Alpha Gestão Documental

from flask import Flask

from .signatures import bp as signatures_bp
from .document_types import bp as document_types_bp
from app.routes import auth, dashboard, documents, document_types, users, approvals, audits, nonconformities, reports, equipments

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    from . import views
    app.register_blueprint(views.bp)

    app.register_blueprint(signatures_bp, url_prefix='/signatures')
    app.register_blueprint(document_types_bp)

    return app

def register_blueprints(app):
    """Registrar todos os blueprints da aplicação"""
    from app.routes import auth, dashboard, users, documents, document_types, groups
    from app.routes import equipments, equipment_types, nonconformities
    from app.routes import audits, approvals, reports, signatures

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp, url_prefix='/dashboard')
    app.register_blueprint(users.bp, url_prefix='/users')
    app.register_blueprint(documents.bp, url_prefix='/documents')
    app.register_blueprint(document_types.bp)
    app.register_blueprint(groups.bp)
    app.register_blueprint(equipments.bp, url_prefix='/equipments')
    app.register_blueprint(equipment_types.bp)
    app.register_blueprint(nonconformities.bp, url_prefix='/nonconformities')
    app.register_blueprint(audits.bp, url_prefix='/audits')
    app.register_blueprint(approvals.bp, url_prefix='/approvals')
    app.register_blueprint(reports.bp, url_prefix='/reports')
    app.register_blueprint(signatures.bp, url_prefix='/signatures')