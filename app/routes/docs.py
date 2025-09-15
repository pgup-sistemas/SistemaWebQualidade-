
from flask import Blueprint, render_template, render_template_string, send_from_directory, current_app
from flask_login import login_required
import os
from pathlib import Path

bp = Blueprint('docs', __name__, url_prefix='/docs')

@bp.route('/')
@login_required 
def index():
    """Página inicial da documentação"""
    return render_template('docs/index.html')

@bp.route('/guia-usuario')
@login_required
def user_guide():
    """Guia do usuário"""
    return render_template('docs/user_guide.html')

@bp.route('/tutoriais')
@login_required
def tutorials():
    """Tutoriais do sistema"""
    return render_template('docs/tutorials.html')

@bp.route('/faq')
@login_required
def faq():
    """Perguntas frequentes"""
    return render_template('docs/faq.html')

@bp.route('/regras-negocio')
@login_required
def business_rules():
    """Regras de negócio"""
    return render_template('docs/business_rules.html')

@bp.route('/index-old')
@login_required 
def index_old():
    """Página inicial da documentação (versão antiga)"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentação - Alpha Gestão</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .doc-card { transition: transform 0.2s; }
        .doc-card:hover { transform: translateY(-2px); }
        .hero-section { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
    </style>
</head>
<body>
    <div class="hero-section py-5">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="display-4"><i class="bi bi-book me-3"></i>Documentação do Sistema</h1>
                    <p class="lead">Guia completo para utilizar o Alpha Gestão Documental</p>
                </div>
                <div class="col-md-4 text-end">
                    <a href="{{ url_for('dashboard.index') }}" class="btn btn-light btn-lg">
                        <i class="bi bi-arrow-left"></i> Voltar ao Sistema
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="container py-5">
        <div class="row g-4">
            <!-- Guia do Usuário -->
            <div class="col-md-6 col-lg-4">
                <div class="card doc-card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-person-check display-3 text-primary mb-3"></i>
                        <h5 class="card-title">Guia do Usuário</h5>
                        <p class="card-text">Aprenda a usar todas as funcionalidades do sistema passo a passo.</p>
                        <a href="#" class="btn btn-primary">Acessar Guia</a>
                    </div>
                </div>
            </div>

            <!-- Manual Técnico -->
            <div class="col-md-6 col-lg-4">
                <div class="card doc-card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-gear display-3 text-success mb-3"></i>
                        <h5 class="card-title">Manual Técnico</h5>
                        <p class="card-text">Informações técnicas sobre arquitetura, API e desenvolvimento.</p>
                        <a href="#" class="btn btn-success">Ver Manual</a>
                    </div>
                </div>
            </div>

            <!-- Perguntas Frequentes -->
            <div class="col-md-6 col-lg-4">
                <div class="card doc-card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-question-circle display-3 text-warning mb-3"></i>
                        <h5 class="card-title">FAQ</h5>
                        <p class="card-text">Respostas para as perguntas mais comuns sobre o sistema.</p>
                        <a href="#" class="btn btn-warning">Ver FAQ</a>
                    </div>
                </div>
            </div>

            <!-- Tutoriais -->
            <div class="col-md-6 col-lg-4">
                <div class="card doc-card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-play-circle display-3 text-info mb-3"></i>
                        <h5 class="card-title">Tutoriais</h5>
                        <p class="card-text">Vídeos e tutoriais passo a passo das principais funcionalidades.</p>
                        <a href="#" class="btn btn-info">Assistir</a>
                    </div>
                </div>
            </div>

            <!-- Regras de Negócio -->
            <div class="col-md-6 col-lg-4">
                <div class="card doc-card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-clipboard-check display-3 text-danger mb-3"></i>
                        <h5 class="card-title">Regras de Negócio</h5>
                        <p class="card-text">Políticas, procedimentos e regras implementadas no sistema.</p>
                        <a href="#" class="btn btn-danger">Consultar</a>
                    </div>
                </div>
            </div>

            <!-- Suporte -->
            <div class="col-md-6 col-lg-4">
                <div class="card doc-card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-headset display-3 text-secondary mb-3"></i>
                        <h5 class="card-title">Suporte</h5>
                        <p class="card-text">Entre em contato para suporte técnico e esclarecimento de dúvidas.</p>
                        <a href="mailto:suporte@alphagestao.com" class="btn btn-secondary">Contatar</a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Seção de início rápido -->
        <div class="row mt-5">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="bi bi-rocket me-2"></i>Início Rápido</h4>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <h6><i class="bi bi-1-circle text-primary me-2"></i>Primeiro Acesso</h6>
                                <p class="small">Faça login com suas credenciais e explore o dashboard.</p>
                            </div>
                            <div class="col-md-4">
                                <h6><i class="bi bi-2-circle text-primary me-2"></i>Crie seu Primeiro Documento</h6>
                                <p class="small">Use os templates predefinidos para criar documentos facilmente.</p>
                            </div>
                            <div class="col-md-4">
                                <h6><i class="bi bi-3-circle text-primary me-2"></i>Configure Notificações</h6>
                                <p class="small">Ajuste suas preferências para receber alertas importantes.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Links úteis -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info">
                    <h6><i class="bi bi-info-circle me-2"></i>Links Úteis</h6>
                    <div class="row">
                        <div class="col-md-3">
                            <a href="{{ url_for('documents.create') }}" class="text-decoration-none">
                                <i class="bi bi-file-plus me-1"></i>Criar Documento
                            </a>
                        </div>
                        <div class="col-md-3">
                            <a href="{{ url_for('documents.index') }}" class="text-decoration-none">
                                <i class="bi bi-files me-1"></i>Meus Documentos
                            </a>
                        </div>
                        <div class="col-md-3">
                            <a href="{{ url_for('reports.index') }}" class="text-decoration-none">
                                <i class="bi bi-graph-up me-1"></i>Relatórios
                            </a>
                        </div>
                        <div class="col-md-3">
                            <a href="{{ url_for('auth.profile') }}" class="text-decoration-none">
                                <i class="bi bi-person-gear me-1"></i>Meu Perfil
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """)

@bp.route('/generate')
@login_required
def generate():
    """Gera a documentação HTML"""
    try:
        import subprocess
        result = subprocess.run(['python', 'generate_docs.py'], 
                              capture_output=True, text=True, cwd=current_app.root_path + '/..')
        
        if result.returncode == 0:
            return {"success": True, "message": "Documentação gerada com sucesso!"}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

@bp.route('/view/<path:filename>')
@login_required
def view_docs(filename):
    """Visualiza arquivos da documentação gerada"""
    docs_path = Path(current_app.root_path).parent / "docs" / "_build" / "html"
    
    if not docs_path.exists():
        return "Documentação não encontrada. Execute a geração primeiro.", 404
    
    return send_from_directory(docs_path, filename)
