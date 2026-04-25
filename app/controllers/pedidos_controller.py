"""
Controller de Pedidos — Café Aroma
Define as rotas da API REST para criação e consulta de pedidos.
"""

import logging
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Pedido, ItemPedido, Produto, Estoque
from app.services import messaging

logger = logging.getLogger(__name__)

# Blueprint: agrupa as rotas de pedidos com prefixo /api/pedidos
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')


@pedidos_bp.route('', methods=['POST'])
def criar_pedido():
    """
    POST /api/pedidos
    Recebe um pedido do front-end, salva no banco de dados,
    envia para a fila RabbitMQ e imprime o cupom na LUOGAO VS-5890C.

    Corpo da requisição (JSON):
        {
            "usuario_id": 1,           (opcional)
            "observacao": "Sem açúcar",
            "itens": [
                {"produto_id": 2, "quantidade": 2},
                {"produto_id": 5, "quantidade": 1}
            ]
        }

    Respostas:
        201 → Pedido criado com sucesso
        400 → Dados inválidos
        404 → Produto não encontrado
        500 → Erro interno
    """
    dados = request.get_json()

    if not dados or 'itens' not in dados or len(dados['itens']) == 0:
        return jsonify({'erro': 'O pedido deve conter ao menos um item.'}), 400

    try:
        # ── 1. Criar o pedido no banco de dados ──────────────────────
        novo_pedido = Pedido(
            usuario_id=dados.get('usuario_id'),
            observacao=dados.get('observacao', ''),
            status='confirmado'
        )
        db.session.add(novo_pedido)
        db.session.flush()  # gera o ID do pedido antes de commitar

        total = 0.0

        # ── 2. Adicionar itens ao pedido ─────────────────────────────
        for item_dados in dados['itens']:
            produto = Produto.query.get(item_dados.get('produto_id'))

            if not produto:
                db.session.rollback()
                return jsonify({'erro': f"Produto ID {item_dados.get('produto_id')} não encontrado."}), 404

            if not produto.ativo:
                db.session.rollback()
                return jsonify({'erro': f"Produto '{produto.nome}' está inativo."}), 400

            quantidade = int(item_dados.get('quantidade', 1))
            preco_unitario = float(produto.preco)

            item = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=preco_unitario
            )
            db.session.add(item)
            total += quantidade * preco_unitario

            # Atualiza o estoque (decrementa)
            estoque = Estoque.query.filter_by(produto_id=produto.id).first()
            if estoque:
                estoque.quantidade = max(0, estoque.quantidade - quantidade)

        # ── 3. Salvar o total e commitar no banco ────────────────────
        novo_pedido.total = total
        db.session.commit()

        # ── 4. Montar dicionário para fila e impressora ──────────────
        dados_pedido = novo_pedido.to_dict()

        # ── 5. Enviar para fila RabbitMQ + imprimir cupom ────────────
        # O messaging.py dispara a impressão em thread paralela
        fila_ok = messaging.enviar_pedido_fila(dados_pedido)

        return jsonify({
            'mensagem': 'Pedido criado com sucesso!',
            'pedido': dados_pedido,
            'fila_rabbitmq': fila_ok
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar pedido: {e}")
        return jsonify({'erro': 'Erro interno ao processar o pedido.'}), 500


@pedidos_bp.route('', methods=['GET'])
def listar_pedidos():
    """
    GET /api/pedidos
    Retorna todos os pedidos cadastrados.
    """
    pedidos = Pedido.query.order_by(Pedido.criado_em.desc()).all()
    return jsonify([p.to_dict() for p in pedidos]), 200


@pedidos_bp.route('/<int:pedido_id>', methods=['GET'])
def obter_pedido(pedido_id: int):
    """
    GET /api/pedidos/<id>
    Retorna os detalhes de um pedido específico.
    """
    pedido = Pedido.query.get_or_404(pedido_id)
    return jsonify(pedido.to_dict()), 200
