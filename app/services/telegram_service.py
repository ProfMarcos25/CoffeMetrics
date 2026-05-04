"""
Servico de Notificacao via Telegram - Cafe Aroma
Envia uma mensagem formatada para um bot do Telegram sempre que um
novo pedido e confirmado.

Como funciona:
  - A API do Telegram funciona via HTTP simples (sem biblioteca extra).
  - O bot recebe o pedido e encaminha para um chat ou grupo configurado.
  - A chamada e feita em background (thread daemon) para nao bloquear a
    resposta HTTP ao cliente.

Ordem de prioridade das configuracoes:
  1. Variaveis de ambiente / .env (via python-dotenv ja carregado no __init__.py)
  2. data/config.json (fallback)

Como criar seu bot e obter o token:
  1. Abra o Telegram e converse com @BotFather
  2. Digite /newbot, escolha nome e username
  3. Copie o TOKEN gerado e cole em .env -> TELEGRAM_BOT_TOKEN

Como obter o CHAT_ID:
  1. Adicione o bot a um grupo OU envie uma mensagem diretamente a ele
  2. Acesse: https://api.telegram.org/bot<TOKEN>/getUpdates
  3. Copie o valor de "id" dentro de "chat" e cole em TELEGRAM_CHAT_ID
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[2] / 'data' / 'config.json'

# URL base da API do Telegram (token substituido em tempo de execucao)
TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def _cfg(chave: str) -> str:
    """
    Le uma configuracao priorizando variaveis de ambiente (os.environ / .env)
    e usando data/config.json como fallback.
    O .env ja deve ter sido carregado pelo __init__.py via load_dotenv().
    """
    valor = os.environ.get(chave, '').strip()
    if valor:
        return valor
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_json = json.load(f)
        return config_json.get(chave, '').strip()
    except Exception:
        return ''


def _formatar_mensagem(dados_pedido: dict[str, Any]) -> str:
    """
    Monta a mensagem HTML formatada que sera enviada ao bot do Telegram.

    O Telegram suporta parse_mode='HTML', que permite usar tags como:
      <b> negrito </b>   <i> italico </i>   <code> codigo </code>

    Parametros:
        dados_pedido: dicionario com os dados do pedido (id, itens, total, etc.)

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
        data_hora = dt.strftime('%d/%m/%Y as %H:%M')
    except Exception:
        data_hora = datetime.now().strftime('%d/%m/%Y as %H:%M')

    # Monta a lista de itens
    linhas_itens = ''
    for item in itens:
        nome = item.get('produto_nome', 'Item')
        qtd = item.get('quantidade', 1)
        preco = float(item.get('preco_unitario', 0))
        subtotal = qtd * preco
        linhas_itens += f"  . {nome} x{qtd} - <b>R$ {subtotal:.2f}</b>\n"

    # Monta a observacao (exibe so se existir)
    obs_linha = f"\n<i>Obs: {observacao}</i>" if observacao else ''

    mensagem = (
        f"<b>CAFE AROMA - Novo Pedido!</b>\n"
        f"---\n"
        f"Pedido: <code>#{pedido_id}</code>\n"
        f"{data_hora}\n"
        f"---\n"
        f"<b>Itens:</b>\n"
        f"{linhas_itens}"
        f"---\n"
        f"<b>Total: R$ {total:.2f}</b>"
        f"{obs_linha}"
    )
    return mensagem


def enviar_notificacao(dados_pedido: dict[str, Any]) -> bool:
    """
    Envia a notificacao do pedido para o bot do Telegram.

    Parametros:
        dados_pedido: dicionario com os dados completos do pedido.

    Retorna:
        True  -> mensagem enviada com sucesso
        False -> falha (token ausente, sem internet, bot inativo, etc.)

    A falha NAO interrompe o fluxo do pedido - apenas registra no log.
    """
    token = _cfg('TELEGRAM_BOT_TOKEN')
    chat_id = _cfg('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        logger.warning(
            "Notificacao Telegram ignorada: TELEGRAM_BOT_TOKEN ou "
            "TELEGRAM_CHAT_ID nao configurados (.env ou config.json)."
        )
        return False

    # Placeholders como SEU_TOKEN_AQUI indicam que ainda nao foi configurado
    if 'SEU_' in token or 'SEU_' in chat_id:
        logger.warning("Notificacao Telegram ignorada: token/chat_id ainda com valor de exemplo.")
        return False

    try:
        import requests

        url = TELEGRAM_API_BASE.format(token=token)
        mensagem = _formatar_mensagem(dados_pedido)

        # Payload da API sendMessage do Telegram
        payload = {
            'chat_id':    chat_id,
            'text':       mensagem,
            'parse_mode': 'HTML',
            'disable_notification': False
        }

        # timeout=10s: evita travar o servidor se o Telegram estiver lento
        resposta = requests.post(url, json=payload, timeout=10)

        if resposta.status_code == 200 and resposta.json().get('ok'):
            logger.info(f"Telegram: notificacao do pedido #{dados_pedido.get('id')} enviada.")
            return True
        else:
            logger.error(
                f"Telegram: API retornou erro - "
                f"status={resposta.status_code} body={resposta.text[:200]}"
            )
            return False

    except Exception as erro:
        logger.error(f"Telegram: erro ao enviar notificacao - {erro}")
        return False


def enviar_notificacao_async(dados_pedido: dict[str, Any]) -> None:
    """
    Dispara a notificacao do Telegram em uma thread separada (daemon).

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