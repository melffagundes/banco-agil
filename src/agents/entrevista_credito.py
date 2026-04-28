import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from src.state import BankState
from src.tools.credit_tools import atualizar_score_cliente
from src.utils.score_calculator import calcular_score

_SYSTEM_PROMPT = (
    "Você conduz uma entrevista financeira para recalcular o score de crédito do cliente. "
    "Colete as seguintes informações uma por vez, de forma conversacional e empática:\n"
    "1. Renda mensal bruta (em R$)\n"
    "2. Tipo de emprego: formal (CLT/concursado), autônomo ou desempregado\n"
    "3. Despesas fixas mensais (em R$)\n"
    "4. Número de dependentes\n"
    "5. Possui dívidas ativas? (sim/não)\n"
    "Após coletar todos os dados, informe ao cliente que o score foi recalculado e retorne ao serviço de crédito. "
    "Nunca mencione transferência de agente."
)

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)


def _extrair_dados_entrevista(dados: dict):
    """Verifica se todos os dados da entrevista foram coletados."""
    campos_necessarios = ["renda_mensal", "tipo_emprego", "despesas_fixas", "num_dependentes", "tem_dividas"]
    if all(k in dados for k in campos_necessarios):
        return dados
    return None


def entrevista_node(state: BankState) -> Command:
    """Nó de entrevista: coleta dados financeiros e recalcula o score do cliente."""
    mensagens = [SystemMessage(content=_SYSTEM_PROMPT)] + state["messages"]
    resposta = _llm.invoke(mensagens)

    conteudo = resposta.content if isinstance(resposta.content, str) else ""
    entrevista_data = state.get("entrevista_data", {}) or {}

    # Tenta extrair informações da entrevista do histórico de mensagens
    # O LLM deve sinalizar quando todos os dados foram coletados com uma palavra-chave
    dados_completos = _extrair_dados_entrevista(entrevista_data)

    if dados_completos:
        try:
            novo_score = calcular_score(
                renda_mensal=float(dados_completos["renda_mensal"]),
                despesas_fixas=float(dados_completos["despesas_fixas"]),
                tipo_emprego=str(dados_completos["tipo_emprego"]).lower(),
                num_dependentes=int(dados_completos["num_dependentes"]),
                tem_dividas=str(dados_completos["tem_dividas"]),  # "sim" | "não"
            )

            cpf = state.get("cliente_cpf", "")
            if cpf:
                atualizar_score_cliente.invoke({"cpf": cpf, "novo_score": novo_score})

            return Command(
                update={
                    "messages": [resposta],
                    "cliente_score": float(novo_score),
                    "current_agent": "credito",
                    "entrevista_data": {},
                },
                goto="credito",
            )
        except Exception as e:
            print(f"Erro ao calcular score: {e}")

    return Command(
        update={"messages": [resposta], "entrevista_data": entrevista_data},
        goto="entrevista",
    )
