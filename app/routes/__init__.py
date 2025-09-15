# Pacote de rotas do Alpha Gestão Documental

from flask import Flask

from .signatures import bp as signatures_bp
from .document_types import bp as document_types_bp

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