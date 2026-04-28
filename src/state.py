from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class BankState(TypedDict):
    messages: Annotated[list, add_messages]   # histórico de mensagens
    authenticated: bool
    cliente_cpf: str
    cliente_nome: str
    cliente_score: float
    cliente_limite: float
    auth_attempts: int                         # máx 3 tentativas
    current_agent: str                         # triagem | credito | entrevista | cambio
    entrevista_data: dict                      # dados coletados na entrevista
    solicitacao_status: str                    # pendente | aprovado | rejeitado
    should_end: bool
