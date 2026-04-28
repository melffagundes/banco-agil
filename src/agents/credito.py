import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from src.state import BankState
from src.tools.credit_tools import (
    consultar_limite,
    verificar_score_para_limite,
    registrar_solicitacao_aumento,
    atualizar_score_cliente,
)

_SYSTEM_PROMPT = (
    "Você é o especialista de crédito do Banco Ágil. "
    "Consulte limites e processe solicitações de aumento de crédito do cliente autenticado. "
    "Se o score for insuficiente para o aumento solicitado, ofereça a opção de entrevista de crédito "
    "para recalcular o score. Nunca mencione transferência de agente. "
    "Se o usuário quiser voltar ou encerrar, sinalize o encerramento."
)

_ferramentas = [consultar_limite, verificar_score_para_limite, registrar_solicitacao_aumento]

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
).bind_tools(_ferramentas)

_mapa_ferramentas = {
    "consultar_limite": consultar_limite,
    "verificar_score_para_limite": verificar_score_para_limite,
    "registrar_solicitacao_aumento": registrar_solicitacao_aumento,
}


def credito_node(state: BankState) -> Command:
    """Nó de crédito: consulta limites e processa solicitações de aumento."""
    mensagens = [SystemMessage(content=_SYSTEM_PROMPT)] + state["messages"]
    resposta = _llm.invoke(mensagens)

    conteudo = resposta.content if isinstance(resposta.content, str) else ""

    # Encerramento
    if any(p in conteudo.lower() for p in ["encerrar", "até logo", "tchau", "encerrando"]):
        return Command(
            update={"messages": [resposta], "should_end": True},
            goto="__end__",
        )

    # Roteamento para entrevista
    if any(p in conteudo.lower() for p in ["entrevista", "recalcular score", "avaliação financeira"]):
        return Command(
            update={"messages": [resposta], "current_agent": "entrevista"},
            goto="entrevista",
        )

    # Processa chamadas de ferramentas
    if resposta.tool_calls:
        msgs_ferramenta = []
        novo_estado = {}

        for chamada in resposta.tool_calls:
            ferramenta = _mapa_ferramentas.get(chamada["name"])
            if ferramenta:
                resultado = ferramenta.invoke(chamada["args"])
                msgs_ferramenta.append(
                    ToolMessage(content=str(resultado), tool_call_id=chamada["id"])
                )

                # Atualiza status de solicitação se registrada
                if chamada["name"] == "verificar_score_para_limite":
                    if isinstance(resultado, dict):
                        status = "aprovado" if resultado.get("aprovado") else "rejeitado"
                        novo_estado["solicitacao_status"] = status

                if chamada["name"] == "registrar_solicitacao_aumento":
                    novo_estado["solicitacao_status"] = "pendente"

        return Command(
            update={"messages": [resposta] + msgs_ferramenta, **novo_estado},
            goto="credito",
        )

    return Command(
        update={"messages": [resposta]},
        goto="credito",
    )
