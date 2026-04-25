"""
Inicialização do app Flask — Café Aroma
Configura as extensões, registra os blueprints e cria o banco de dados.
"""

import json
import logging
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Instância global do banco de dados (importada pelos models e controllers)
db = SQLAlchemy()

# Caminho para o arquivo de configuração
CONFIG_PATH = Path(__file__).resolve().parent.parent / 'data' / 'config.json'


def criar_app() -> Flask:
    """
    Factory function: cria e configura a aplicação Flask.

    O padrão Application Factory permite criar múltiplas instâncias
    do app (ex: uma para produção e outra para testes).
    """
    app = Flask(__name__)

    # ── Carrega configurações do config.json ─────────────────────────
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    app.config['SECRET_KEY'] = config.get('SECRET_KEY', 'cafearoma-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get(
        'DATABASE_URI',
        'postgresql://postgres:senha@localhost:5432/cafearoma'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Configura o logger ───────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # ── Inicializa extensões ─────────────────────────────────────────
    db.init_app(app)

    # ── Registra os Blueprints (grupos de rotas) ─────────────────────
    from app.controllers.pedidos_controller import pedidos_bp
    from app.controllers.produtos_controller import produtos_bp
    from app.controllers.analytics_controller import analytics_bp

    app.register_blueprint(pedidos_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(analytics_bp)

    # ── Rota principal (serve o front-end) ───────────────────────────
    from flask import render_template

    @app.route('/')
    def index():
        """Serve a página principal do Café Aroma."""
        return render_template('index.html')

    # ── Cria as tabelas no banco de dados (se não existirem) ─────────
    with app.app_context():
        from app.models import models  # noqa: importa para registrar os models
        db.create_all()

    return app
