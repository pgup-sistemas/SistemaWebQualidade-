
#!/usr/bin/env python3
"""
Script para gerar a documentação do sistema Alpha Gestão Documental
"""

import os
import subprocess
import sys
from pathlib import Path

def check_sphinx_installed():
    """Verifica se o Sphinx está instalado"""
    try:
        import sphinx
        print("✓ Sphinx encontrado")
        return True
    except ImportError:
        print("❌ Sphinx não encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", 
                       "sphinx", "sphinx-rtd-theme", "sphinxcontrib-mermaid"])
        return True

def create_docs_structure():
    """Cria a estrutura de pastas da documentação"""
    docs_dir = Path("docs")
    
    # Criar diretórios necessários
    dirs_to_create = [
        "docs/_static",
        "docs/_templates", 
        "docs/funcionalidades",
        "docs/usuarios",
        "docs/api",
        "docs/desenvolvimento"
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Diretório criado: {dir_path}")

def generate_api_docs():
    """Gera documentação automática da API"""
    os.chdir("docs")
    
    # Gerar documentação automática dos módulos
    try:
        subprocess.run([
            "sphinx-apidoc", 
            "-o", "api", 
            "../app",
            "--force",
            "--module-first"
        ], check=True)
        print("✓ Documentação da API gerada")
    except subprocess.CalledProcessError:
        print("❌ Erro ao gerar documentação da API")
    except FileNotFoundError:
        print("❌ sphinx-apidoc não encontrado")

def build_html_docs():
    """Constrói a documentação HTML"""
    try:
        # Limpar build anterior
        subprocess.run(["make", "clean"], check=True)
        print("✓ Build anterior limpo")
        
        # Gerar HTML
        subprocess.run(["make", "html"], check=True)
        print("✓ Documentação HTML gerada")
        
        # Mostrar localização
        html_path = Path("_build/html/index.html").absolute()
        print(f"\n🎉 Documentação gerada com sucesso!")
        print(f"📁 Localização: {html_path}")
        print(f"🌐 Abra no navegador: file://{html_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao gerar documentação: {e}")
    except FileNotFoundError:
        print("❌ Make não encontrado. Usando sphinx-build diretamente...")
        
        # Fallback usando sphinx-build diretamente
        try:
            subprocess.run([
                "sphinx-build", 
                "-b", "html", 
                ".", 
                "_build/html"
            ], check=True)
            print("✓ Documentação HTML gerada com sphinx-build")
        except:
            print("❌ Erro ao usar sphinx-build")

def create_additional_files():
    """Cria arquivos adicionais da documentação"""
    
    # Criar arquivo de instalação
    install_content = """
Instalação e Configuração
=========================

Requisitos do Sistema
====================

**Software:**
* Python 3.11 ou superior  
* PostgreSQL 15 ou superior
* Navegador web moderno

**Hardware (mínimo):**
* 2GB RAM
* 10GB espaço em disco
* Processador dual-core

Instalação no Replit
===================

1. **Clone o repositório**
2. **Configure as variáveis de ambiente:**
   * DATABASE_URL
   * SECRET_KEY  
   * MAIL_SERVER (opcional)

3. **Execute a migração:**
   ```bash
   python migrate_db_complete.py
   ```

4. **Inicie o sistema:**
   ```bash
   python run.py
   ```

Configuração Inicial
==================

1. **Primeiro acesso**: admin/admin123
2. **Altere a senha padrão**
3. **Configure os grupos/setores**
4. **Crie os tipos de documentos**
5. **Cadastre os usuários**

Variáveis de Ambiente
===================

```env
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=sua-chave-super-secreta
FLASK_ENV=production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-app
```

Backup e Restore
===============

**Backup automático:**
* Executado diariamente
* Armazenado em local seguro
* Inclui dados e arquivos

**Restore manual:**
```bash
pg_restore -d database backup_file.dump
```
"""
    
    with open("docs/instalacao.rst", "w", encoding="utf-8") as f:
        f.write(install_content)
    
    print("✓ Arquivo de instalação criado")

def main():
    """Função principal"""
    print("🚀 Iniciando geração da documentação...")
    
    # Verificar dependências
    if not check_sphinx_installed():
        sys.exit(1)
    
    # Criar estrutura
    create_docs_structure()
    
    # Criar arquivos adicionais
    create_additional_files()
    
    # Gerar documentação da API
    generate_api_docs()
    
    # Construir documentação
    build_html_docs()
    
    print("\n📚 Documentação completa gerada!")
    print("💡 Para atualizar: execute este script novamente")
    print("🔧 Para customizar: edite os arquivos .rst em docs/")

if __name__ == "__main__":
    main()
