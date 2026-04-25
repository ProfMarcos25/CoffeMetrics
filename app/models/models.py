"""
Modelos do banco de dados — Café Aroma
Cada classe representa uma tabela no PostgreSQL.
Utiliza SQLAlchemy como ORM (Object-Relational Mapper).
"""

from datetime import datetime
from app import db


class Usuario(db.Model):
    """
    Tabela: usuarios
    Armazena os clientes e operadores do sistema.
    """
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    perfil = db.Column(db.String(20), default='cliente')          # 'cliente' ou 'operador'
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)

    def to_dict(self):
        """Retorna o usuário como dicionário (sem a senha)."""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'perfil': self.perfil,
            'criado_em': self.criado_em.isoformat()
        }


class Produto(db.Model):
    """
    Tabela: produtos
    Catálogo de itens vendidos na cafeteria.
    """
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50))                          # ex: 'bebida', 'salgado'
    ativo = db.Column(db.Boolean, default=True)
    imagem_url = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    itens_pedido = db.relationship('ItemPedido', backref='produto', lazy=True)
    estoque = db.relationship('Estoque', backref='produto', uselist=False, lazy=True)

    def to_dict(self):
        """Retorna o produto como dicionário."""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': float(self.preco),
            'categoria': self.categoria,
            'ativo': self.ativo,
            'imagem_url': self.imagem_url
        }


class Pedido(db.Model):
    """
    Tabela: pedidos
    Registra cada venda realizada na cafeteria.
    """
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    status = db.Column(db.String(30), default='pendente')         # pendente, confirmado, cancelado
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    observacao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Retorna o pedido como dicionário, incluindo seus itens."""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'status': self.status,
            'total': float(self.total),
            'observacao': self.observacao,
            'criado_em': self.criado_em.isoformat(),
            'itens': [item.to_dict() for item in self.itens]
        }


class ItemPedido(db.Model):
    """
    Tabela: itens_pedido
    Cada linha representa um produto dentro de um pedido.
    """
    __tablename__ = 'itens_pedido'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # preço no momento da venda

    def to_dict(self):
        """Retorna o item de pedido como dicionário."""
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else '',
            'quantidade': self.quantidade,
            'preco_unitario': float(self.preco_unitario),
            'subtotal': float(self.quantidade * self.preco_unitario)
        }


class Estoque(db.Model):
    """
    Tabela: estoque
    Controla a quantidade disponível de cada produto.
    """
    __tablename__ = 'estoque'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), unique=True, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    quantidade_minima = db.Column(db.Integer, default=5)          # alerta de estoque baixo
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Retorna o estoque como dicionário."""
        return {
            'id': self.id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else '',
            'quantidade': self.quantidade,
            'quantidade_minima': self.quantidade_minima,
            'estoque_baixo': self.quantidade <= self.quantidade_minima
        }
