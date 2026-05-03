"""
Serviço de Notificação via Telegram — Café Aroma
Envia uma mensagem formatada para um bot do Telegram sempre que um
novo pedido é confirmado.

Como funciona:
  - A API do Telegram funciona via HTTP simples (sem biblioteca extra).
  - O bot recebe o pedido e encaminha para um chat ou grupo configurado.
  - A chamada é feita em background (thread daemon) para não bloquear a
    resposta HTTP ao cliente.

Como criar seu bot e obter o token:
  1. Abra o Telegram e converse com @BotFather
  2. Digite /newbot, escolha nome e username
  3. Copie o TOKEN gerado e cole em data/config.json → TELEGRAM_BOT_TOKEN

Como obter o CHAT_ID:
  1. Adicione o bot a um grupo OU envie uma mensagem diretamente a ele
  2. Acesse: https://api.telegram.org/bot<TOKEN>/getUpdates
  3. Copie o valor de "id" dentro de "chat" e cole em TELEGRAM_CHAT_ID
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

# Usa requests para chamar a API HTTP do Telegram (sem biblioteca extra)
try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False
    logging.warning("requests não encontrado. Notificações Telegram desativadas.")

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[2] / 'data' / 'config.json'

# URL base da API do Telegram — substitui <TOKEN> pelo token real em tempo de execução
TELEGRAM_API_URL = "https://api.telegram.org/bot8756218296:AAGjYY8tCs0rmFY0d_4dNsixZxWIL-ffIwQ/sendMessage"


def _carregar_config() -> dict[str, Any]:
    """Lê as configurações do arquivo data/config.json."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _formatar_mensagem(dados_pedido: dict[str, Any]) -> str:
    """
    Monta a mensagem HTML formatada que será enviada ao bot do Telegram.

    O Telegram suporta parse_mode='HTML', que permite usar tags como:
      <b> negrito </b>   <i> itálico </i>   <code> código </code>

    Parâmetros:
        dados_pedido: dicionário com os dados do pedido (id, itens, total, etc.)

    Retorna:
        String com a mensagem pronta para envio.
    """
    pedido_id = dados_pedido.get('id', '?')
    itens = dados_pedido.get('itens', [])
    total = float(dados_pedido.get('total', 0))
    observacao = dados_pedido.get('observacao', '').strip()

    # Formata data/hora
    try:
        dt = datetime.fromisoformat(dados_pedido.get('criado_em', ''))
        data_hora = dt.strftime('%d/%m/%Y às %H:%M')
    except Exception:
        data_hora = datetime.now().strftime('%d/%m/%Y às %H:%M')

    # Monta a lista de itens
    linhas_itens = ''
    for item in itens:
        nome = item.get('produto_nome', 'Item')
        qtd = item.get('quantidade', 1)
        preco = float(item.get('preco_unitario', 0))
        subtotal = qtd * preco
        linhas_itens += f"  • {nome} x{qtd} — <b>R$ {subtotal:.2f}</b>\n"

    # Monta a observação (exibe só se existir)
    obs_linha = f"\n📝 <i>Obs: {observacao}</i>" if observacao else ''

    mensagem = (
        f"☕ <b>CAFÉ AROMA — Novo Pedido!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 Pedido: <code>#{pedido_id}</code>\n"
        f"🕐 {data_hora}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Itens:</b>\n"
        f"{linhas_itens}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Total: R$ {total:.2f}</b>"
        f"{obs_linha}"
    )
    return mensagem


def enviar_notificacao(dados_pedido: dict[str, Any]) -> bool:
    """
    Envia a notificação do pedido para o bot do Telegram.

    Parâmetros:
        dados_pedido: dicionário com os dados completos do pedido.

    Retorna:
        True  → mensagem enviada com sucesso
        False → falha (token ausente, sem internet, bot inativo, etc.)

    A falha NÃO interrompe o fluxo do pedido — apenas registra no log.
    """
    if not REQUESTS_DISPONIVEL:
        logger.warning("Notificação Telegram ignorada: requests não instalado.")
        return False

    try:
        config = _carregar_config()
        token = config.get('TELEGRAM_BOT_TOKEN', '').strip()
        chat_id = config.get('TELEGRAM_CHAT_ID', '').strip()

        if not token or not chat_id:
            logger.warning(
                "Notificação Telegram ignorada: TELEGRAM_BOT_TOKEN ou "
                "TELEGRAM_CHAT_ID não configurados em data/config.json."
            )
            return False

        url = TELEGRAM_API_URL.format(token=token)
        mensagem = _formatar_mensagem(dados_pedido)

        # Payload da API sendMessage do Telegram
        payload = {
            'chat_id':    chat_id,
            'text':       mensagem,
            'parse_mode': 'HTML',        # interpreta tags <b>, <i>, <code>
            'disable_notification': False  # True = mensagem silenciosa
        }

        # timeout=10s: evita travar o servidor se o Telegram estiver lento
        resposta = requests.post(url, json=payload, timeout=10)

        if resposta.status_code == 200 and resposta.json().get('ok'):
            logger.info(f"Telegram: notificação do pedido #{dados_pedido.get('id')} enviada.")
            return True
        else:
            logger.error(
                f"Telegram: API retornou erro — "
                f"status={resposta.status_code} body={resposta.text[:200]}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error("Telegram: timeout ao tentar enviar a notificação.")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Telegram: sem conexão com a internet.")
        return False
    except Exception as erro:
        logger.error(f"Telegram: erro inesperado — {erro}")
        return False


def enviar_notificacao_async(dados_pedido: dict[str, Any]) -> None:
    """
    Dispara a notificação do Telegram em uma thread separada (daemon).

    Uso no controller:
        telegram_service.enviar_notificacao_async(dados_pedido)

    A thread daemon encerra automaticamente quando o processo principal termina,
    sem bloquear o servidor Flask nem a resposta HTTP ao cliente.
    """
    thread = threading.Thread(
        target=enviar_notificacao,
        args=(dados_pedido,),
        daemon=True,
        name=f"telegram-pedido-{dados_pedido.get('id', '?')}"
    )
    thread.start()
    logger.info(f"Thread Telegram iniciada para pedido #{dados_pedido.get('id')}.")
