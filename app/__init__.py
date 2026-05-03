"""
Inicializacao do app Flask - Cafe Aroma
Configura as extensoes, registra os blueprints e cria o banco de dados.

Ordem de prioridade das configuracoes:
  1. Variaveis de ambiente / arquivo .env (via python-dotenv)
  2. data/config.json (fallback)
"""

import json
import logging
import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Carrega o .env na raiz do projeto para os.environ
_ENV_PATH = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=_ENV_PATH)

# Instancia global do banco de dados (importada pelos models e controllers)
db = SQLAlchemy()

# Caminho para o arquivo de configuracao JSON (fallback)
CONFIG_PATH = Path(__file__).resolve().parent.parent / 'data' / 'config.json'


def _cfg(config_json: dict, chave: str, padrao: str = '') -> str:
    """Le uma configuracao: .env/env-var tem prioridade sobre config.json."""
    return os.environ.get(chave) or config_json.get(chave) or padrao


def criar_app() -> Flask:
    """
    Factory function: cria e configura a aplicacao Flask.

    O padrao Application Factory permite criar multiplas instancias
    do app (ex: uma para producao e outra para testes).
    """
    app = Flask(__name__)

    # -- Carrega config.json como fallback --------------------------------
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_json = json.load(f)

    db_uri = _cfg(config_json, 'DATABASE_URI')
    if not db_uri:
        raise RuntimeError(
            "DATABASE_URI nao configurada!\n"
            "Defina-a no arquivo .env (recomendado) ou em data/config.json."
        )

    app.config['SECRET_KEY']                  = _cfg(config_json, 'SECRET_KEY', 'cafearoma-dev')
    app.config['SQLALCHEMY_DATABASE_URI']     = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -- Configura o logger -----------------------------------------------
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # -- Inicializa extensoes ---------------------------------------------
    db.init_app(app)

    # -- Registra os Blueprints (grupos de rotas) -------------------------
    from app.controllers.pedidos_controller import pedidos_bp
    from app.controllers.produtos_controller import produtos_bp
    from app.controllers.analytics_controller import analytics_bp

    app.register_blueprint(pedidos_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(analytics_bp)

    # -- Rota principal (serve o front-end) -------------------------------
    from flask import render_template

    @app.route('/')
    def index():
        """Serve a pagina principal do Cafe Aroma."""
        return render_template('index.html')

    # -- Cria as tabelas no banco de dados (se nao existirem) -------------
    with app.app_context():
        from app.models import models  # noqa: importa para registrar os models
        db.create_all()

    return app