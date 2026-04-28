from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import BankState
from src.agents.triagem import triagem_node
from src.agents.credito import credito_node
from src.agents.entrevista_credito import entrevista_node
from src.agents.cambio import cambio_node


def _deve_encerrar(state: BankState) -> str:
    """Roteamento condicional: encerra se should_end=True."""
    if state.get("should_end"):
        return "__end__"
    return state.get("current_agent", "triagem")


def criar_grafo(checkpointer=None) -> StateGraph:
    """
    Cria e compila o grafo LangGraph do Banco Ágil.

    Fluxo:
        START → triagem → [credito | entrevista | cambio | END]
        credito → [entrevista | END]
        entrevista → credito
    """
    builder = StateGraph(BankState)

    # Adiciona nós
    builder.add_node("triagem", triagem_node)
    builder.add_node("credito", credito_node)
    builder.add_node("entrevista", entrevista_node)
    builder.add_node("cambio", cambio_node)

    # Entrada sempre pelo triagem
    builder.add_edge(START, "triagem")

    # Os nós usam Command para roteamento dinâmico interno
    # LangGraph processa o goto do Command automaticamente

    if checkpointer:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


def criar_grafo_com_memoria() -> StateGraph:
    """Cria o grafo com MemorySaver para persistência de sessão."""
    return criar_grafo(checkpointer=MemorySaver())
