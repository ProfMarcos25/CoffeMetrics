"""
Controller de Analytics — Café Aroma
Rotas para consulta de previsão de demanda e rankings de produtos.
"""

from flask import Blueprint, jsonify, request
from app.models.models import ItemPedido, Produto
from app.services.analytics import prever_demanda, analisar_produtos_mais_vendidos
from app import db
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/previsao/<int:produto_id>', methods=['GET'])
def previsao_demanda(produto_id: int):
    """
    GET /api/analytics/previsao/<produto_id>
    Retorna a previsão de demanda para o próximo período de um produto.

    Usa regressão linear treinada com o histórico de vendas diárias.
    """
    produto = Produto.query.get_or_404(produto_id)

    # Agrupa as vendas por dia (período) para treinar o modelo
    historico = (
        db.session.query(
            func.date(ItemPedido.pedido.has()),
            func.sum(ItemPedido.quantidade)
        )
        .filter(ItemPedido.produto_id == produto_id)
        .group_by(func.date(ItemPedido.pedido))
        .all()
    )

    # Converte para o formato esperado pelo serviço de analytics
    dados_historico = [
        {'periodo': i + 1, 'quantidade': int(qtd)}
        for i, (_, qtd) in enumerate(historico)
    ]

    resultado = prever_demanda(dados_historico)
    resultado['produto'] = produto.nome
    resultado['produto_id'] = produto_id

    return jsonify(resultado), 200


@analytics_bp.route('/mais-vendidos', methods=['GET'])
def mais_vendidos():
    """
    GET /api/analytics/mais-vendidos?top=5
    Retorna o ranking dos produtos mais vendidos.
    """
    top_n = request.args.get('top', 5, type=int)

    itens = db.session.query(
        ItemPedido.produto_id,
        Produto.nome,
        func.sum(ItemPedido.quantidade).label('total')
    ).join(Produto).group_by(ItemPedido.produto_id, Produto.nome).all()

    dados = [{'produto_nome': nome, 'quantidade': int(total)} for _, nome, total in itens]
    ranking = analisar_produtos_mais_vendidos(dados, top_n=top_n)

    return jsonify(ranking), 200
