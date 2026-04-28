import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Banco Ágil — Atendimento Virtual",
    page_icon="🏦",
    layout="centered",
)

st.title("🏦 Banco Ágil — Atendimento Virtual")


def inicializar_sessao():
    """Inicializa o estado da sessão Streamlit."""
    if "grafo" not in st.session_state:
        from src.graph import criar_grafo_com_memoria
        st.session_state.grafo = criar_grafo_com_memoria()

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    if "historico" not in st.session_state:
        st.session_state.historico = []

    if "encerrado" not in st.session_state:
        st.session_state.encerrado = False

    if "cliente_info" not in st.session_state:
        st.session_state.cliente_info = None


def obter_estado_atual() -> dict:
    """Obtém o estado atual do grafo via checkpointer."""
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    try:
        estado = st.session_state.grafo.get_state(config)
        return estado.values if estado else {}
    except Exception:
        return {}


def enviar_mensagem(texto: str):
    """Envia mensagem ao grafo e atualiza o histórico."""
    st.session_state.historico.append({"role": "user", "content": texto})

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    entrada = {"messages": [HumanMessage(content=texto)]}

    try:
        resultado = st.session_state.grafo.invoke(entrada, config=config)

        # Pega a última mensagem do assistente
        mensagens = resultado.get("messages", [])
        resposta_texto = ""
        for msg in reversed(mensagens):
            if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
                if hasattr(msg, "role") and msg.role == "tool":
                    continue
                resposta_texto = msg.content
                break

        if resposta_texto:
            st.session_state.historico.append({"role": "assistant", "content": resposta_texto})

        # Atualiza informações do cliente se autenticado
        if resultado.get("authenticated"):
            st.session_state.cliente_info = {
                "nome": resultado.get("cliente_nome", ""),
                "score": resultado.get("cliente_score", 0),
                "limite": resultado.get("cliente_limite", 0),
            }

        # Verifica encerramento
        if resultado.get("should_end"):
            st.session_state.encerrado = True

    except Exception as e:
        st.session_state.historico.append({
            "role": "assistant",
            "content": f"Desculpe, ocorreu um erro no atendimento. Por favor, tente novamente.",
        })
        print(f"Erro ao invocar grafo: {e}")


def reiniciar_atendimento():
    """Reinicia o atendimento zerando a sessão."""
    for chave in ["grafo", "thread_id", "historico", "encerrado", "cliente_info"]:
        if chave in st.session_state:
            del st.session_state[chave]
    st.rerun()


# Inicializa sessão
inicializar_sessao()

# === SIDEBAR ===
with st.sidebar:
    st.header("Informações do Atendimento")

    if st.session_state.cliente_info:
        info = st.session_state.cliente_info
        st.success(f"**Cliente autenticado**")
        st.write(f"**Nome:** {info['nome']}")
        st.write(f"**Score:** {info['score']:.0f}")
        st.write(f"**Limite atual:** R$ {info['limite']:,.2f}")
    else:
        st.info("Aguardando autenticação...")

    st.divider()

    if st.button("🔄 Encerrar Atendimento", use_container_width=True):
        reiniciar_atendimento()

    st.divider()
    st.caption("Banco Ágil © 2024 — Powered by LangGraph + Groq")

# === CHAT PRINCIPAL ===

# Mensagem inicial se histórico vazio
if not st.session_state.historico:
    with st.chat_message("assistant"):
        st.write(
            "Olá! Bem-vindo ao Banco Ágil. Sou seu atendente virtual. "
            "Para começarmos, preciso verificar sua identidade. "
            "Por favor, informe seu CPF e data de nascimento."
        )

# Exibe histórico de mensagens
for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Encerramento
if st.session_state.encerrado:
    st.info("Atendimento encerrado. Clique em '🔄 Encerrar Atendimento' para iniciar um novo.")
else:
    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Aguarde..."):
                enviar_mensagem(prompt)

        # Exibe última resposta do assistente
        if st.session_state.historico and st.session_state.historico[-1]["role"] == "assistant":
            st.rerun()
