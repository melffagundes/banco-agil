import requests
from langchain_core.tools import tool


@tool
def consultar_cotacao(moeda: str = "USD") -> dict:
    """
    Busca a cotação de uma moeda estrangeira em relação ao BRL usando a AwesomeAPI.
    Exemplos de moedas: USD, EUR, GBP, JPY, ARS, BTC.
    Retorna: moeda, cotacao_compra, cotacao_venda, timestamp.
    """
    moeda = moeda.upper().strip()
    url = f"https://economia.awesomeapi.com.br/last/{moeda}-BRL"

    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()

        chave = f"{moeda}BRL"
        if chave not in dados:
            return {"erro": f"Moeda '{moeda}' não encontrada. Verifique o código e tente novamente."}

        cotacao = dados[chave]
        return {
            "moeda": moeda,
            "cotacao_compra": float(cotacao["bid"]),
            "cotacao_venda": float(cotacao["ask"]),
            "timestamp": cotacao["create_date"],
        }
    except requests.exceptions.Timeout:
        return {"erro": "Serviço de cotação indisponível no momento. Tente novamente em instantes."}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro ao consultar cotação: {str(e)}"}
    except Exception as e:
        return {"erro": f"Erro inesperado: {str(e)}"}
