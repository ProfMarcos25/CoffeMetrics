"""
Controller de Produtos — Café Aroma
Rotas para consulta e gerenciamento do catálogo de produtos.
Suporta operações CRUD completas: Create, Read, Update, Delete.
"""

import logging
from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Produto, Estoque

logger = logging.getLogger(__name__)

produtos_bp = Blueprint('produtos', __name__, url_prefix='/api/produtos')


@produtos_bp.route('', methods=['GET'])
def listar_produtos():
    """
    GET /api/produtos
    Retorna todos os produtos ativos do cardápio (visão do PDV).
    """
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.categoria, Produto.nome).all()
    return jsonify([p.to_dict() for p in produtos]), 200


@produtos_bp.route('/admin', methods=['GET'])
def listar_produtos_admin():
    """
    GET /api/produtos/admin
    Retorna TODOS os produtos (ativos e inativos) para o painel de gerenciamento.
    Inclui dados de estoque em cada produto.
    """
    produtos = Produto.query.order_by(Produto.categoria, Produto.nome).all()

    resultado = []
    for p in produtos:
        dados = p.to_dict()
        # Adiciona informações de estoque
        if p.estoque:
            dados['estoque_quantidade'] = p.estoque.quantidade
            dados['estoque_minimo'] = p.estoque.quantidade_minima
            dados['estoque_baixo'] = p.estoque.quantidade <= p.estoque.quantidade_minima
        else:
            dados['estoque_quantidade'] = 0
            dados['estoque_minimo'] = 5
            dados['estoque_baixo'] = True
        resultado.append(dados)

    return jsonify(resultado), 200


@produtos_bp.route('/<int:produto_id>', methods=['GET'])
def obter_produto(produto_id: int):
    """
    GET /api/produtos/<id>
    Retorna os detalhes de um produto específico.
    """
    produto = Produto.query.get_or_404(produto_id)
    dados = produto.to_dict()
    if produto.estoque:
        dados['estoque_quantidade'] = produto.estoque.quantidade
        dados['estoque_minimo'] = produto.estoque.quantidade_minima
    return jsonify(dados), 200


@produtos_bp.route('', methods=['POST'])
def criar_produto():
    """
    POST /api/produtos
    Cadastra um novo produto no catálogo.

    Corpo JSON:
        {
            "nome": "Café Expresso",
            "preco": 5.50,
            "categoria": "bebida",
            "descricao": "Café curto e encorpado",
            "imagem_url": "",
            "estoque_inicial": 50,
            "estoque_minimo": 10
        }
    """
    dados = request.get_json()
    if not dados or not dados.get('nome') or dados.get('preco') is None:
        return jsonify({'erro': 'Nome e preço são obrigatórios.'}), 400

    try:
        produto = Produto(
            nome=dados['nome'].strip(),
            preco=float(dados['preco']),
            descricao=dados.get('descricao', '').strip(),
            categoria=dados.get('categoria', 'outros'),
            imagem_url=dados.get('imagem_url', '').strip(),
            ativo=dados.get('ativo', True)
        )
        db.session.add(produto)
        db.session.flush()  # gera o ID sem commitar

        # Cria o registro de estoque para o novo produto
        estoque = Estoque(
            produto_id=produto.id,
            quantidade=int(dados.get('estoque_inicial', 0)),
            quantidade_minima=int(dados.get('estoque_minimo', 5))
        )
        db.session.add(estoque)
        db.session.commit()

        logger.info(f"Produto '{produto.nome}' (ID {produto.id}) cadastrado.")
        return jsonify(produto.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar produto: {e}")
        return jsonify({'erro': 'Erro interno ao cadastrar produto.'}), 500


@produtos_bp.route('/<int:produto_id>', methods=['PUT'])
def atualizar_produto(produto_id: int):
    """
    PUT /api/produtos/<id>
    Atualiza os dados de um produto existente.

    Corpo JSON (todos os campos são opcionais):
        {
            "nome": "Novo Nome",
            "preco": 7.00,
            "categoria": "bebida",
            "descricao": "Nova descrição",
            "ativo": true,
            "estoque_quantidade": 30,
            "estoque_minimo": 5
        }
    """
    produto = Produto.query.get_or_404(produto_id)
    dados = request.get_json()

    if not dados:
        return jsonify({'erro': 'Nenhum dado enviado.'}), 400

    try:
        # Atualiza apenas os campos enviados
        if 'nome' in dados:
            produto.nome = dados['nome'].strip()
        if 'preco' in dados:
            produto.preco = float(dados['preco'])
        if 'descricao' in dados:
            produto.descricao = dados['descricao'].strip()
        if 'categoria' in dados:
            produto.categoria = dados['categoria']
        if 'imagem_url' in dados:
            produto.imagem_url = dados['imagem_url'].strip()
        if 'ativo' in dados:
            produto.ativo = bool(dados['ativo'])

        # Atualiza o estoque se enviado
        if produto.estoque:
            if 'estoque_quantidade' in dados:
                produto.estoque.quantidade = int(dados['estoque_quantidade'])
            if 'estoque_minimo' in dados:
                produto.estoque.quantidade_minima = int(dados['estoque_minimo'])
        else:
            # Cria estoque se não existir
            estoque = Estoque(
                produto_id=produto.id,
                quantidade=int(dados.get('estoque_quantidade', 0)),
                quantidade_minima=int(dados.get('estoque_minimo', 5))
            )
            db.session.add(estoque)

        db.session.commit()
        logger.info(f"Produto ID {produto_id} atualizado.")

        result = produto.to_dict()
        if produto.estoque:
            result['estoque_quantidade'] = produto.estoque.quantidade
            result['estoque_minimo'] = produto.estoque.quantidade_minima
        return jsonify(result), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar produto {produto_id}: {e}")
        return jsonify({'erro': 'Erro interno ao atualizar produto.'}), 500


@produtos_bp.route('/<int:produto_id>', methods=['DELETE'])
def deletar_produto(produto_id: int):
    """
    DELETE /api/produtos/<id>
    Remove um produto do banco de dados.

    Se o produto possui pedidos vinculados, ele é desativado (soft delete)
    em vez de removido, para preservar o histórico de vendas.
    """
    produto = Produto.query.get_or_404(produto_id)

    try:
        # Verifica se há itens de pedido vinculados a este produto
        from app.models.models import ItemPedido
        tem_pedidos = ItemPedido.query.filter_by(produto_id=produto_id).first()

        if tem_pedidos:
            # Soft delete: desativa o produto sem apagar do banco
            produto.ativo = False
            db.session.commit()
            logger.info(f"Produto ID {produto_id} desativado (soft delete — possui pedidos vinculados).")
            return jsonify({
                'mensagem': f"Produto '{produto.nome}' desativado pois possui pedidos vinculados.",
                'soft_delete': True
            }), 200
        else:
            # Hard delete: remove completamente
            nome = produto.nome
            db.session.delete(produto)
            db.session.commit()
            logger.info(f"Produto '{nome}' (ID {produto_id}) removido permanentemente.")
            return jsonify({
                'mensagem': f"Produto '{nome}' removido com sucesso.",
                'soft_delete': False
            }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar produto {produto_id}: {e}")
        return jsonify({'erro': 'Erro interno ao remover produto.'}), 500
