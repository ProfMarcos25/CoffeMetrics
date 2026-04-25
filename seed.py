"""
Script para popular o banco de dados com dados de exemplo — Café Aroma
Execute com: python seed.py

Seguro para rodar mais de uma vez: verifica duplicatas antes de inserir.
"""

from app import criar_app, db
from app.models.models import Produto, Estoque, Usuario

app = criar_app()

DADOS_PRODUTOS = [
    {'nome': 'Café Expresso',       'preco': 5.50,  'categoria': 'bebida',  'descricao': 'Café curto e encorpado'},
    {'nome': 'Cappuccino',          'preco': 8.00,  'categoria': 'bebida',  'descricao': 'Espresso com leite vaporizado'},
    {'nome': 'Latte',               'preco': 9.00,  'categoria': 'bebida',  'descricao': 'Espresso com muito leite'},
    {'nome': 'Café com Leite',      'preco': 6.50,  'categoria': 'bebida',  'descricao': 'Tradicional café com leite'},
    {'nome': 'Chocolate Quente',    'preco': 9.50,  'categoria': 'bebida',  'descricao': 'Chocolate cremoso'},
    {'nome': 'Suco de Laranja',     'preco': 7.00,  'categoria': 'bebida',  'descricao': 'Natural, 300ml'},
    {'nome': 'Pão de Queijo',       'preco': 4.50,  'categoria': 'salgado', 'descricao': 'Mineiro, 3 unidades'},
    {'nome': 'Coxinha',             'preco': 6.00,  'categoria': 'salgado', 'descricao': 'Frango com catupiry'},
    {'nome': 'Croissant',           'preco': 7.50,  'categoria': 'salgado', 'descricao': 'Manteiga e presunto'},
    {'nome': 'Bolo de Cenoura',     'preco': 8.00,  'categoria': 'doce',    'descricao': 'Com cobertura de chocolate'},
    {'nome': 'Fatia de Cheesecake', 'preco': 10.00, 'categoria': 'doce',    'descricao': 'Com calda de frutas vermelhas'},
    {'nome': 'Brigadeiro',          'preco': 3.50,  'categoria': 'doce',    'descricao': 'Artesanal'},
]

try:
    with app.app_context():
        print("🌱 Populando banco de dados...")

        inseridos = 0
        ignorados = 0

        for dados in DADOS_PRODUTOS:
            # Evita duplicata: verifica se já existe produto com o mesmo nome
            existe = Produto.query.filter_by(nome=dados['nome']).first()
            if existe:
                print(f"   ⏭️  Produto '{dados['nome']}' já existe — ignorado.")
                ignorados += 1
                continue

            produto = Produto(**dados)
            db.session.add(produto)
            db.session.flush()  # gera o ID antes de criar o estoque

            estoque = Estoque(produto_id=produto.id, quantidade=50, quantidade_minima=10)
            db.session.add(estoque)
            inseridos += 1

        # Usuário operador padrão (verifica duplicata pelo e-mail)
        usuario_ok = False
        if not Usuario.query.filter_by(email='operador@cafearoma.com').first():
            operador = Usuario(
                nome='Operador Café',
                email='operador@cafearoma.com',
                senha_hash='hashed_senha_aqui',  # Em produção: use werkzeug.security
                perfil='operador'
            )
            db.session.add(operador)
            usuario_ok = True

        db.session.commit()

        print(f"\n✅ Seed concluído!")
        print(f"   • Produtos inseridos : {inseridos}")
        print(f"   • Produtos ignorados : {ignorados}")
        print(f"   • Operador criado    : {'Sim' if usuario_ok else 'Já existia'}")

except Exception as erro:
    print(f"\n❌ Erro ao popular o banco de dados: {erro}")
    print("   Verifique se o PostgreSQL está rodando e se o data/config.json está configurado corretamente.")
