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
    """Register all blueprints"""
    from .auth import bp as auth_bp
    from .dashboard import bp as dashboard_bp
    from .documents import bp as documents_bp
    from .document_types import bp as document_types_bp
    from .users import bp as users_bp
    from .groups import bp as groups_bp
    from .approvals import bp as approvals_bp
    from .nonconformities import bp as nonconformities_bp
    from .audits import bp as audits_bp
    from .equipments import bp as equipments_bp
    from .equipment_types import bp as equipment_types_bp
    from .reports import bp as reports_bp
    from .signatures import bp as signatures_bp
    from .docs import bp as docs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(document_types_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(approvals_bp)
    app.register_blueprint(nonconformities_bp)
    app.register_blueprint(audits_bp)
    app.register_blueprint(equipments_bp)
    app.register_blueprint(equipment_types_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(signatures_bp)
    app.register_blueprint(docs_bp)