"""
Serviço de Mensageria — Café Aroma
Integra o sistema com o RabbitMQ usando a biblioteca pika.

RabbitMQ é um message broker: funciona como uma fila de mensagens entre
o servidor Flask (produtor) e outros serviços (consumidores).

Fluxo:
  1. O cliente faz um pedido → Flask salva no banco de dados
  2. Flask publica o pedido na fila RabbitMQ (produtor)
  3. Um serviço consumidor processa a fila de forma assíncrona
  4. Simultaneamente, dispara a impressão do cupom
"""

import json
import logging
import threading
from pathlib import Path

# Tenta importar pika (cliente Python para RabbitMQ)
try:
    import pika
    PIKA_DISPONIVEL = True
except ImportError:
    PIKA_DISPONIVEL = False
    logging.warning("pika não encontrado. Mensageria RabbitMQ desativada.")

from app.services import printer_service

# Configuração do logger
logger = logging.getLogger(__name__)

# Caminho para o arquivo de configuração
CONFIG_PATH = Path(__file__).resolve().parents[2] / 'data' / 'config.json'


def _carregar_config() -> dict:
    """Lê as configurações do arquivo data/config.json."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _criar_conexao_rabbitmq():
    """
    Cria e retorna uma conexão com o servidor RabbitMQ.

    Utiliza credenciais do config.json para autenticação.
    Retorna None se a conexão falhar.
    """
    config = _carregar_config()
    try:
        credenciais = pika.PlainCredentials(
            username=config.get('RABBITMQ_USER', 'guest'),
            password=config.get('RABBITMQ_PASSWORD', 'guest')
        )
        parametros = pika.ConnectionParameters(
            host=config.get('RABBITMQ_HOST', 'localhost'),
            port=int(config.get('RABBITMQ_PORT', 5672)),
            credentials=credenciais,
            # heartbeat: mantém a conexão ativa (em segundos)
            heartbeat=600,
            # blocked_connection_timeout: tempo máximo de espera
            blocked_connection_timeout=300
        )
        conexao = pika.BlockingConnection(parametros)
        return conexao
    except Exception as erro:
        logger.error(f"Falha ao conectar ao RabbitMQ: {erro}")
        return None


def enviar_pedido_fila(dados_pedido: dict) -> bool:
    """
    Publica os dados de um pedido na fila RabbitMQ E aciona a impressão do cupom.

    Parâmetros:
        dados_pedido (dict): Dicionário com os dados completos do pedido.

    Retorna:
        True  → mensagem publicada com sucesso na fila
        False → falha na conexão (o pedido já foi salvo no banco de dados)

    Como funciona o RabbitMQ:
        - channel.queue_declare: garante que a fila existe antes de publicar
        - basic_publish: envia a mensagem para a exchange padrão ('')
        - delivery_mode=2: torna a mensagem persistente (sobrevive a reinicializações)
    """
    config = _carregar_config()
    nome_fila = config.get('RABBITMQ_QUEUE', 'pedidos_queue')

    # ── 1. Disparar a impressão em thread separada ───────────────────
    # A impressão ocorre de forma paralela para não bloquear a resposta HTTP
    thread_impressao = threading.Thread(
        target=printer_service.gerar_recibo,
        args=(dados_pedido,),
        daemon=True   # encerra junto com o processo principal
    )
    thread_impressao.start()
    logger.info(f"Thread de impressão iniciada para pedido #{dados_pedido.get('id')}")

    # ── 2. Publicar na fila RabbitMQ ─────────────────────────────────
    if not PIKA_DISPONIVEL:
        logger.warning("Mensageria ignorada: pika não instalado.")
        return False

    conexao = _criar_conexao_rabbitmq()
    if conexao is None:
        return False

    try:
        canal = conexao.channel()

        # Declara a fila como durável: ela sobrevive a reinicializações do RabbitMQ
        canal.queue_declare(queue=nome_fila, durable=True)

        # Converte o pedido para JSON (formato de mensagem)
        mensagem = json.dumps(dados_pedido, ensure_ascii=False, default=str)

        # Publica a mensagem na fila
        canal.basic_publish(
            exchange='',               # exchange padrão (direct)
            routing_key=nome_fila,     # nome da fila de destino
            body=mensagem.encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2,       # 2 = mensagem persistente no disco
                content_type='application/json'
            )
        )

        logger.info(f"Pedido #{dados_pedido.get('id')} publicado na fila '{nome_fila}'.")
        return True

    except Exception as erro:
        logger.error(f"Erro ao publicar pedido na fila RabbitMQ: {erro}")
        return False

    finally:
        # Sempre fecha a conexão ao finalizar
        try:
            conexao.close()
        except Exception:
            pass


def consumir_fila():
    """
    Inicia o consumidor da fila RabbitMQ (modo de escuta contínua).

    Este método é executado em um processo/thread separado.
    Cada mensagem recebida é processada pela função _processar_pedido.

    Uso: rodar como script separado para escalar o processamento de pedidos.
    """
    if not PIKA_DISPONIVEL:
        logger.error("Impossível consumir fila: pika não instalado.")
        return

    config = _carregar_config()
    nome_fila = config.get('RABBITMQ_QUEUE', 'pedidos_queue')

    conexao = _criar_conexao_rabbitmq()
    if conexao is None:
        return

    canal = conexao.channel()
    canal.queue_declare(queue=nome_fila, durable=True)

    # prefetch_count=1: processa uma mensagem por vez (balanceamento de carga)
    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(queue=nome_fila, on_message_callback=_processar_pedido)

    logger.info(f"Aguardando pedidos na fila '{nome_fila}'...")
    canal.start_consuming()


def _processar_pedido(canal, method, properties, body):
    """
    Callback executado quando um pedido chega na fila.

    Parâmetros (injetados pelo pika):
        canal     → canal de comunicação com o RabbitMQ
        method    → metadados da entrega (ex: delivery_tag para ACK)
        properties→ propriedades da mensagem
        body      → corpo da mensagem em bytes

    ACK (acknowledgment): confirma para o RabbitMQ que a mensagem foi processada.
    Se não enviar o ACK, o RabbitMQ reenvia a mensagem para outro consumidor.
    """
    try:
        dados = json.loads(body.decode('utf-8'))
        logger.info(f"Processando pedido #{dados.get('id')} da fila...")
        # Aqui poderia acionar notificações, relatórios, etc.

        # Confirma o processamento da mensagem (ACK)
        canal.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as erro:
        logger.error(f"Erro ao processar mensagem da fila: {erro}")
        # NACK: não confirma → mensagem volta para a fila
        canal.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
