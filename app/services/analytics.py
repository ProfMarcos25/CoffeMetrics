"""
Serviço de Analytics (IA) — Café Aroma
Utiliza scikit-learn para prever a demanda de produtos.

Regressão Linear:
  - É um algoritmo de aprendizado de máquina supervisionado.
  - Dado um conjunto de dados históricos (vendas por dia/hora),
    aprende a relação entre as variáveis e faz previsões.
  - Fórmula: y = β₀ + β₁·x  (y = demanda prevista, x = período)
"""

import logging
import numpy as np

# Tenta importar scikit-learn e pandas
try:
    from sklearn.linear_model import LinearRegression
    import pandas as pd
    SK_DISPONIVEL = True
except ImportError:
    SK_DISPONIVEL = False
    logging.warning("scikit-learn ou pandas não encontrados. Analytics desativada.")

logger = logging.getLogger(__name__)


def prever_demanda(historico_vendas: list) -> dict:
    """
    Prevê a demanda futura de um produto com base no histórico de vendas.

    Parâmetros:
        historico_vendas (list): Lista de dicionários com:
            - 'periodo' (int): número do dia/semana/mês (variável independente X)
            - 'quantidade' (int): quantidade vendida (variável dependente y)

    Retorna:
        dict com:
            - 'previsao_proximo_periodo' (float): quantidade prevista
            - 'coeficiente_angular' (float): taxa de crescimento/queda por período
            - 'r2_score' (float): precisão do modelo (0.0 a 1.0)
            - 'erro' (str | None): mensagem de erro, se houver

    Exemplo de uso:
        historico = [
            {'periodo': 1, 'quantidade': 20},
            {'periodo': 2, 'quantidade': 25},
            {'periodo': 3, 'quantidade': 22},
        ]
        resultado = prever_demanda(historico)
        # resultado['previsao_proximo_periodo'] → ~23.7
    """
    if not SK_DISPONIVEL:
        return {'erro': 'scikit-learn não instalado', 'previsao_proximo_periodo': None}

    if len(historico_vendas) < 2:
        return {'erro': 'Dados insuficientes (mínimo 2 períodos)', 'previsao_proximo_periodo': None}

    try:
        # Converte para arrays numpy (formato exigido pelo scikit-learn)
        # reshape(-1, 1): transforma array 1D em coluna 2D → [[1], [2], [3]]
        X = np.array([item['periodo'] for item in historico_vendas]).reshape(-1, 1)
        y = np.array([item['quantidade'] for item in historico_vendas])

        # Cria e treina o modelo de regressão linear
        modelo = LinearRegression()
        modelo.fit(X, y)

        # Prevê o próximo período (último + 1)
        proximo_periodo = np.array([[int(X[-1][0]) + 1]])
        previsao = modelo.predict(proximo_periodo)[0]

        # R² Score: mede a qualidade do modelo
        # 1.0 = perfeito | 0.0 = não explica nada | < 0 = pior que a média
        r2 = modelo.score(X, y)

        return {
            'previsao_proximo_periodo': round(float(previsao), 2),
            'coeficiente_angular': round(float(modelo.coef_[0]), 4),
            'intercepto': round(float(modelo.intercept_), 4),
            'r2_score': round(r2, 4),
            'erro': None
        }

    except Exception as e:
        logger.error(f"Erro ao prever demanda: {e}")
        return {'erro': str(e), 'previsao_proximo_periodo': None}


def analisar_produtos_mais_vendidos(itens_pedidos: list, top_n: int = 5) -> list:
    """
    Analisa e retorna os produtos mais vendidos em ordem decrescente.

    Parâmetros:
        itens_pedidos (list): Lista de dicionários com 'produto_nome' e 'quantidade'.
        top_n (int): Número máximo de produtos a retornar (padrão: 5).

    Retorna:
        Lista de dicionários com 'produto' e 'total_vendido', ordenada por volume.
    """
    if not SK_DISPONIVEL:
        return []

    try:
        df = pd.DataFrame(itens_pedidos)
        if df.empty or 'produto_nome' not in df.columns:
            return []

        ranking = (
            df.groupby('produto_nome')['quantidade']
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
        )

        return [
            {'produto': row['produto_nome'], 'total_vendido': int(row['quantidade'])}
            for _, row in ranking.iterrows()
        ]

    except Exception as e:
        logger.error(f"Erro ao analisar produtos mais vendidos: {e}")
        return []
