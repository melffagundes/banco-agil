import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from src.state import BankState
from src.tools.exchange_tools import consultar_cotacao

_SYSTEM_PROMPT = (
    "Você é o especialista de câmbio do Banco Ágil. "
    "Consulte cotações de moedas estrangeiras em tempo real e apresente ao cliente de forma clara, "
    "indicando os valores de compra e venda em reais (BRL). "
    "Moedas disponíveis: USD (dólar americano), EUR (euro), GBP (libra), JPY (iene), ARS (peso argentino), BTC (bitcoin). "
    "Nunca mencione transferência de agente. "
    "Se o usuário quiser encerrar ou voltar, sinalize o encerramento."
)

_ferramentas = [consultar_cotacao]

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
).bind_tools(_ferramentas)


def cambio_node(state: BankState) -> Command:
    """Nó de câmbio: consulta cotações de moedas em tempo real."""
    mensagens = [SystemMessage(content=_SYSTEM_PROMPT)] + state["messages"]
    resposta = _llm.invoke(mensagens)

    conteudo = resposta.content if isinstance(resposta.content, str) else ""

    # Encerramento
    if any(p in conteudo.lower() for p in ["encerrar", "até logo", "tchau", "encerrando"]):
        return Command(
            update={"messages": [resposta], "should_end": True},
            goto="__end__",
        )

    # Processa chamadas de ferramentas
    if resposta.tool_calls:
        msgs_ferramenta = []

        for chamada in resposta.tool_calls:
            if chamada["name"] == "consultar_cotacao":
                resultado = consultar_cotacao.invoke(chamada["args"])
                msgs_ferramenta.append(
                    ToolMessage(content=str(resultado), tool_call_id=chamada["id"])
                )

        return Command(
            update={"messages": [resposta] + msgs_ferramenta},
            goto="cambio",
        )

    return Command(
        update={"messages": [resposta]},
        goto="cambio",
    )
