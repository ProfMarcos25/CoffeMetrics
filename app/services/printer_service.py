"""
Serviço de Impressão Térmica — Café Aroma
Utiliza a biblioteca python-escpos para comunicar com a LUOGAO VS-5890C (58mm).

Protocolo ESC/POS:
  - Comandos ESC (Escape) controlam formatação: negrito, alinhamento, etc.
  - Comandos POS (Point of Sale) controlam ações: corte de papel, QR Code, etc.
  - O papel de 58mm suporta no máximo 32 caracteres por linha em fonte normal.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Tenta importar a biblioteca python-escpos
# Caso não esteja instalada, o sistema registra o erro mas não interrompe o fluxo
try:
    from escpos.printer import Usb, Network, Serial
    ESCPOS_DISPONIVEL = True
except ImportError:
    ESCPOS_DISPONIVEL = False
    logging.warning("python-escpos não encontrada. Impressão desativada.")

# Configuração do logger — registra eventos e erros da impressora
logger = logging.getLogger(__name__)

# Caminho para o arquivo de configuração do projeto
CONFIG_PATH = Path(__file__).resolve().parents[2] / 'data' / 'config.json'

# Largura máxima do papel de 58mm em caracteres (fonte normal)
LARGURA_LINHA = 32


def _carregar_config() -> dict:
    """
    Lê o arquivo data/config.json e retorna as configurações como dicionário.
    """
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _conectar_impressora():
    """
    Cria e retorna a conexão com a impressora LUOGAO VS-5890C.

    A interface pode ser:
      - USB:     conecta via Vendor ID e Product ID (identificadores do hardware USB)
      - Network: conecta via IP e porta TCP (impressora em rede Wi-Fi/Ethernet)

    Retorna None se a conexão falhar.
    """
    config = _carregar_config()
    interface = config.get('PRINTER_INTERFACE', 'USB').upper()

    try:
        if interface == 'USB':
            # Converte os IDs hexadecimais string para inteiros
            vendor_id = int(config.get('PRINTER_VENDOR_ID', '0x0416'), 16)
            product_id = int(config.get('PRINTER_PRODUCT_ID', '0x5011'), 16)
            impressora = Usb(vendor_id, product_id)
        elif interface == 'NETWORK':
            host = config.get('PRINTER_HOST', '192.168.1.100')
            porta = config.get('PRINTER_PORT', 9100)
            impressora = Network(host, porta)
        else:
            logger.error(f"Interface de impressora desconhecida: {interface}")
            return None

        return impressora

    except Exception as erro:
        # Se a impressora estiver offline ou desconectada, registra o erro
        logger.error(f"Falha ao conectar à impressora: {erro}")
        return None


def _centralizar(texto: str) -> str:
    """
    Centraliza o texto dentro da largura de 32 caracteres.
    Exemplo: '  CAFÉ AROMA  '
    """
    return texto.center(LARGURA_LINHA)


def _linha_separadora() -> str:
    """Retorna uma linha de traços para separar seções do cupom."""
    return '-' * LARGURA_LINHA


def _formatar_item_linha(nome: str, qtd: int, preco: float) -> str:
    """
    Formata uma linha de item respeitando o limite de 32 caracteres.
    Exemplo: 'Café Expresso x2     R$ 10,00'
    """
    valor_str = f"R${preco * qtd:>7.2f}"
    item_str = f"{nome[:14]} x{qtd}"                 # trunca nome longo
    espaco = LARGURA_LINHA - len(item_str) - len(valor_str)
    return item_str + (' ' * max(espaco, 1)) + valor_str


def gerar_recibo(dados_pedido: dict) -> bool:
    """
    Gera e imprime o recibo do pedido na impressora térmica LUOGAO VS-5890C.

    Parâmetros:
        dados_pedido (dict): Dicionário com os dados do pedido, contendo:
            - id (int): ID do pedido
            - itens (list): Lista de dicionários com 'produto_nome', 'quantidade', 'preco_unitario'
            - total (float): Valor total do pedido
            - criado_em (str): Data/hora do pedido no formato ISO

    Retorna:
        True  → impressão realizada com sucesso
        False → impressora offline ou erro (o pedido prossegue normalmente no sistema)

    Fluxo ESC/POS:
        1. Conecta à impressora via USB ou Network
        2. Configura alinhamento centralizado e imprime o cabeçalho
        3. Imprime data, hora e lista de itens
        4. Imprime o total em negrito
        5. Gera QR Code com o ID do pedido
        6. Avança o papel e executa o corte
    """
    if not ESCPOS_DISPONIVEL:
        logger.warning("Impressão ignorada: python-escpos não instalada.")
        return False

    impressora = _conectar_impressora()
    if impressora is None:
        logger.error(f"Impressora offline. Pedido #{dados_pedido.get('id')} não impresso.")
        return False

    try:
        pedido_id = dados_pedido.get('id', '?')
        itens = dados_pedido.get('itens', [])
        total = dados_pedido.get('total', 0.0)

        # Tenta analisar a data do pedido
        try:
            data_pedido = datetime.fromisoformat(dados_pedido.get('criado_em', ''))
            data_str = data_pedido.strftime('%d/%m/%Y %H:%M')
        except Exception:
            data_str = datetime.now().strftime('%d/%m/%Y %H:%M')

        # ── CABEÇALHO ──────────────────────────────────────────────
        # align='center' → ESC a 1 (centraliza o texto)
        impressora.set(align='center', bold=True, double_height=True, double_width=True)
        impressora.text('CAFÉ AROMA\n')

        impressora.set(align='center', bold=False, double_height=False, double_width=False)
        impressora.text('Cafeteria Inteligente\n')
        impressora.text(_linha_separadora() + '\n')

        # ── DATA E HORA ────────────────────────────────────────────
        impressora.set(align='left')
        impressora.text(f'Data: {data_str}\n')
        impressora.text(f'Pedido Nº: {pedido_id}\n')
        impressora.text(_linha_separadora() + '\n')

        # ── LISTA DE ITENS ─────────────────────────────────────────
        impressora.text('ITENS\n')
        for item in itens:
            nome = item.get('produto_nome', 'Item')
            qtd = item.get('quantidade', 1)
            preco = float(item.get('preco_unitario', 0))
            linha = _formatar_item_linha(nome, qtd, preco)
            impressora.text(linha + '\n')

        impressora.text(_linha_separadora() + '\n')

        # ── TOTAL EM NEGRITO ───────────────────────────────────────
        # bold=True → ESC E 1 (ativa negrito)
        impressora.set(align='right', bold=True)
        impressora.text(f'TOTAL: R$ {float(total):.2f}\n')
        impressora.set(bold=False)
        impressora.text(_linha_separadora() + '\n')

        # ── QR CODE ────────────────────────────────────────────────
        # O QR Code é gerado pelo comando GS ( k do protocolo ESC/POS
        # Codifica o ID do pedido para rastreamento
        impressora.set(align='center')
        impressora.text('Escaneie para detalhes:\n')
        qr_conteudo = f'CAFEAROMA-PEDIDO-{pedido_id}'
        impressora.qr(qr_conteudo, size=4)

        # ── RODAPÉ ─────────────────────────────────────────────────
        impressora.text('\nObrigado pela visita!\n')
        impressora.text('    Volte sempre :)    \n')

        # ── CORTE DO PAPEL ─────────────────────────────────────────
        # feed(4) → avança 4 linhas antes do corte (ESC d 4)
        # cut()   → executa o corte total do papel (GS V 0)
        impressora.feed(4)
        impressora.cut()

        logger.info(f"Recibo do pedido #{pedido_id} impresso com sucesso.")
        return True

    except Exception as erro:
        # Erro durante a impressão → registra mas não interrompe o sistema
        logger.error(f"Erro ao imprimir pedido #{dados_pedido.get('id')}: {erro}")
        return False
