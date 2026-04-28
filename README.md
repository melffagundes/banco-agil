# 🏦 Banco Ágil — Sistema de Atendimento Bancário com IA

## Visão Geral

O **Banco Ágil** é um sistema de atendimento bancário inteligente que utiliza **LangGraph** para orquestrar múltiplos agentes de IA especializados, apresentando ao cliente uma experiência unificada de atendimento. A interface é construída com **Streamlit** e o modelo de linguagem utilizado é o **Llama 3.3 70B** via **Groq API** (gratuita e de alta velocidade).

---

## Arquitetura

### Fluxo dos Agentes

```
                        +------------------+
                        |      START       |
                        +--------+---------+
                                 |
                        +--------v---------+
                        |    TRIAGEM       |  ← Autentica via CPF + data nasc.
                        +--------+---------+
                                 |
              +------------------+------------------+
              |                  |                   |
     +--------v-------+  +-------v--------+  +------v--------+
     |    CRÉDITO     |  |   ENTREVISTA   |  |    CÂMBIO     |
     | Consulta/aum.  |  | Coleta dados   |  | Cotação em    |
     | de limite      |  | financeiros e  |  | tempo real    |
     +--------+-------+  | recalc. score  |  +------+--------+
              |          +-------+--------+         |
              |                  |                   |
              +------------------+-------------------+
                                 |
                        +--------v---------+
                        |       END        |
                        +------------------+
```

**Fluxo do grafo:**
- `START → triagem → [credito | entrevista | cambio | END]`
- `credito → [entrevista | END]`
- `entrevista → credito`

### Como os Dados são Manipulados

| Arquivo | Operação | Responsável |
|---------|----------|-------------|
| `data/clientes.csv` | Leitura (autenticação/consulta), Escrita (atualização de score) | `auth_tools.py`, `credit_tools.py` |
| `data/score_limite.csv` | Leitura (verificação de elegibilidade) | `credit_tools.py` |
| `data/solicitacoes_aumento_limite.csv` | Escrita (registro de pedidos) — gerado em runtime | `credit_tools.py` |

Todas as operações de CSV usam `pandas` com tratamento de erros via `csv_tools.py`. O estado da conversa é mantido em memória pelo `MemorySaver` do LangGraph, isolado por `thread_id` de sessão.

---

## Funcionalidades Implementadas

- **Autenticação segura** — CPF + data de nascimento, máximo 3 tentativas
- **Consulta de limite** — exibe score e limite atual do cliente autenticado
- **Solicitação de aumento de limite** — verifica elegibilidade pelo score via `score_limite.csv`
- **Registro formal de solicitação** — grava em `solicitacoes_aumento_limite.csv` com status `pendente`, `aprovado` ou `rejeitado`
- **Entrevista de crédito** — coleta 5 dados financeiros e recalcula score com fórmula ponderada
- **Atualização de score** — persiste novo score em `clientes.csv` após entrevista
- **Cotação de câmbio** — USD, EUR, GBP, JPY, ARS, BTC em tempo real via AwesomeAPI
- **Interface de chat** — Streamlit com histórico de mensagens e sidebar com dados do cliente
- **Persistência de sessão** — LangGraph MemorySaver mantém contexto da conversa

---

## Desafios e Soluções

| Desafio | Solução |
|---------|---------|
| Roteamento dinâmico entre agentes | `Command(goto=...)` do LangGraph — cada nó retorna o próximo destino explicitamente |
| Estado compartilhado entre agentes | `BankState` (TypedDict) centralizado em `state.py`, passado pelo grafo |
| Cliente não perceber troca de agente | System prompts que proíbem mencionar transferência; contexto de mensagens unificado |
| Máximo de tentativas de autenticação | Campo `auth_attempts` no estado, verificado a cada ciclo do nó triagem |
| Score calculável sem LLM | Função pura `calcular_score()` em `utils/score_calculator.py`, testável de forma independente |
| API de câmbio gratuita e sem API key | AwesomeAPI (`economia.awesomeapi.com.br`) — sem cadastro, sem limite de requisições |

---

## Escolhas Técnicas

- **LangGraph** — permite grafos de agentes com estado, roteamento condicional e ciclos (`entrevista → credito`)
- **Streamlit** — prototipagem rápida de chat UI com gerenciamento de sessão via `st.session_state`
- **Groq + Llama 3.3 70B** — API gratuita, baixa latência (~0.5 s), suporte nativo a tool calling
- **AwesomeAPI** — API de câmbio pública e gratuita, sem necessidade de cadastro ou chave
- **Pandas + CSV** — persistência simples para dados de clientes e solicitações, sem necessidade de banco de dados

---

## Pré-requisitos

- **Python 3.10+**
- Conta gratuita na [Groq Console](https://console.groq.com) para obter a `GROQ_API_KEY`

---

## Tutorial de Execução

```bash
# 1. Clonar o repositório
git clone https://github.com/melffagundes/banco-agil.git
cd banco-agil

# 2. Criar e ativar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variável de ambiente
cp .env.example .env
# Edite o arquivo .env e insira sua GROQ_API_KEY:
#   GROQ_API_KEY=gsk_...

# 5. Executar a aplicação
streamlit run app.py
```

Acesse no navegador: **http://localhost:8501**

---

## Executar Testes

```bash
# Com o ambiente virtual ativado:
python3 -m pytest tests/ -v
```

---

## Cenários de Teste Sugeridos

### Autenticação
| CPF | Data de Nascimento | Cliente | Score | Limite Atual |
|-----|--------------------|---------|-------|--------------|
| `123.456.789-00` | `1990-05-15` | João Silva | 750 | R$ 5.000 |
| `222.333.444-55` | `2000-01-25` | Pedro Alves | 280 | R$ 1.000 |
| `666.777.888-99` | `1975-04-17` | Juliana Pereira | 910 | R$ 25.000 |

### Fluxo de Crédito
1. Autentique com `123.456.789-00` / `1990-05-15` → João Silva (score 750)
2. Peça para ver seu limite → exibe R$ 5.000
3. Solicite aumento para **R$ 15.000** → **aprovado** (score 750 permite até R$ 15.000)
4. Solicite aumento para **R$ 20.000** → **rejeitado** (acima do limite para score 750)
5. Aceite a entrevista de crédito → responda as perguntas → score recalculado → tente novamente

### Fluxo de Câmbio
- Pergunte a cotação do dólar (USD), euro (EUR) ou bitcoin (BTC)

### Falha de Autenticação
- Tente 3 vezes com dados errados → sistema encerra o atendimento educadamente

---

## Estrutura do Projeto

```
banco-agil/
├── app.py                          # Interface Streamlit
├── requirements.txt
├── .env.example
├── data/
│   ├── clientes.csv                # 10 clientes fictícios
│   ├── score_limite.csv            # Tabela score × limite máximo
│   └── solicitacoes_aumento_limite.csv  # Gerado em runtime
├── src/
│   ├── state.py                    # BankState (TypedDict compartilhado)
│   ├── graph.py                    # Grafo LangGraph principal
│   ├── agents/
│   │   ├── triagem.py
│   │   ├── credito.py
│   │   ├── entrevista_credito.py
│   │   └── cambio.py
│   ├── tools/
│   │   ├── csv_tools.py            # Leitura/escrita segura de CSVs
│   │   ├── auth_tools.py           # Autenticação do cliente
│   │   ├── credit_tools.py         # Operações de crédito
│   │   └── exchange_tools.py       # Cotação de câmbio
│   └── utils/
│       └── score_calculator.py     # Fórmula pura de cálculo de score
└── tests/
    ├── test_auth.py
    ├── test_credit.py
    ├── test_score.py
    ├── test_graph.py
    └── fixtures/
        ├── clientes_test.csv
        └── score_limite_test.csv
```
