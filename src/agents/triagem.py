import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.types import Command
from src.state import BankState
from src.tools.auth_tools import autenticar_cliente

_SYSTEM_PROMPT = (
    "Você é o atendente virtual do Banco Ágil. Sua função é autenticar o cliente coletando "
    "CPF e data de nascimento (formato YYYY-MM-DD), e direcioná-lo ao serviço correto. "
    "Seja cordial e objetivo. Nunca mencione que está transferindo para outro agente — "
    "o cliente deve sentir que está conversando com um único atendente. "
    "Após autenticar com sucesso, pergunte em que pode ajudar: crédito/limite ou câmbio. "
    "Se o usuário quiser encerrar, encerre cordialmente."
)

_ferramentas = [autenticar_cliente]

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
).bind_tools(_ferramentas)


def triagem_node(state: BankState) -> Command:
    """Nó de triagem: autentica o cliente e roteia para o serviço solicitado."""
    mensagens = [SystemMessage(content=_SYSTEM_PROMPT)] + state["messages"]
    resposta = _llm.invoke(mensagens)

    # Verifica se o agente solicitou encerramento
    conteudo = resposta.content if isinstance(resposta.content, str) else ""
    if any(p in conteudo.lower() for p in ["encerrar", "até logo", "tchau", "encerrando"]):
        return Command(
            update={"messages": [resposta], "should_end": True},
            goto="__end__",
        )

    # Processa chamadas de ferramentas (autenticação)
    if resposta.tool_calls:
        resultados = []
        novo_estado = {}

        for chamada in resposta.tool_calls:
            if chamada["name"] == "autenticar_cliente":
                resultado = autenticar_cliente.invoke(chamada["args"])
                resultados.append(resultado)

                if resultado.get("autenticado"):
                    novo_estado = {
                        "authenticated": True,
                        "cliente_nome": resultado["nome"],
                        "cliente_score": resultado["score"],
                        "cliente_limite": resultado["limite"],
                        "cliente_cpf": chamada["args"].get("cpf", ""),
                        "current_agent": "triagem",
                    }
                else:
                    tentativas = state.get("auth_attempts", 0) + 1
                    novo_estado = {"auth_attempts": tentativas}

                    if tentativas >= 3:
                        return Command(
                            update={
                                "messages": [resposta],
                                "auth_attempts": tentativas,
                                "should_end": True,
                            },
                            goto="__end__",
                        )

        from langchain_core.messages import ToolMessage
        msgs_ferramenta = [
            ToolMessage(
                content=str(r),
                tool_call_id=state["messages"][-1].id if hasattr(state["messages"][-1], "id") else "tool_call",
            )
            for r in resultados
        ]

        return Command(
            update={"messages": [resposta] + msgs_ferramenta, **novo_estado},
            goto="triagem",
        )

    # Sem chamadas de ferramenta — verifica se já autenticado e redireciona
    if state.get("authenticated"):
        texto = conteudo.lower()
        if any(p in texto for p in ["crédito", "credito", "limite", "aumento"]):
            return Command(
                update={"messages": [resposta], "current_agent": "credito"},
                goto="credito",
            )
        if any(p in texto for p in ["câmbio", "cambio", "cotação", "moeda", "dólar", "euro"]):
            return Command(
                update={"messages": [resposta], "current_agent": "cambio"},
                goto="cambio",
            )

    return Command(
        update={"messages": [resposta]},
        goto="triagem",
    )
