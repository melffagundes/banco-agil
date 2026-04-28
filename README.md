# Banco Agil — Sistema de Atendimento Bancario com IA

## Visao Geral

O Banco Agil e um sistema de atendimento bancario inteligente que utiliza **LangGraph** para orquestrar multiplos agentes de IA especializados, apresentando ao cliente uma experiencia unificada de atendimento. A interface e construida com **Streamlit** e o modelo de linguagem utilizado e o **Llama 3.3 70B** via **Groq API** (gratuita e de alta velocidade).

## Arquitetura

```
                        +------------------+
                        |      START       |
                        +--------+---------+
                                 |
                        +--------v---------+
                        |    TRIAGEM       |  <- Autentica via CPF + data nasc.
                        +--------+---------+
                                 |
              +------------------+------------------+
              |                  |                   |
     +--------v-------+  +-------v--------+  +------v--------+
     |    CREDITO     |  |    ENTREVISTA  |  |    CAMBIO     |
     | Consulta/aum.  |  | Coleta dados   |  | Cotacao em    |
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
- `START -> triagem -> [credito | entrevista | cambio | END]`
- `credito -> [entrevista | END]`
- `entrevista -> credito`

## Funcionalidades Implementadas

- **Autenticacao segura** — CPF + data de nascimento, maximo 3 tentativas
- **Consulta de limite** — exibe score e limite atual do cliente
- **Solicitacao de aumento de limite** — verifica elegibilidade pelo score
- **Entrevista de credito** — coleta dados financeiros e recalcula score
- **Cotacao de cambio** — USD, EUR, GBP, JPY, ARS, BTC em tempo real
- **Interface de chat** — estilo WhatsApp com sidebar de informacoes do cliente
- **Persistencia de sessao** — LangGraph MemorySaver mantem contexto da conversa

## Desafios e Solucoes

| Desafio | Solucao |
|---------|---------|
| Roteamento dinamico entre agentes | `Command(goto=...)` do LangGraph para cada no retornar o proximo destino |
| Estado compartilhado entre agentes | `TypedDict` centralizado em `state.py` passado pelo grafo |
| Cliente nao perceber troca de agente | System prompts que proibem mencionar transferencia; contexto unificado |
| Maximo de tentativas de auth | Campo `auth_attempts` no estado, verificado em cada ciclo do triagem |
| Score calculavel sem LLM | Funcao pura `calcular_score()` testavel independentemente |

## Escolhas Tecnicas

- **LangGraph** — permite grafos de agentes com estado, roteamento condicional e ciclos (entrevista -> credito)
- **Streamlit** — prototipagem rapida de chat UI com gerenciamento de sessao via `st.session_state`
- **Groq + Llama 3.3 70B** — API gratuita, baixa latencia (~0.5s), excelente suporte nativo a tool calling
- **AwesomeAPI** — API de cambio publica e gratuita, sem necessidade de cadastro ou API key
- **Pandas + CSV** — persistencia simples para dados de clientes e solicitacoes, sem necessidade de banco de dados

## Tutorial de Execucao

```bash
git clone <repo>
cd banco_agil
pip install -r requirements.txt
cp .env.example .env
# Edite .env com sua GROQ_API_KEY (obtenha gratuitamente em console.groq.com)
streamlit run app.py
```

## Executar Testes

```bash
pytest tests/ -v
```

## Cenarios de Teste Sugeridos

1. **Autenticacao valida:** CPF `123.456.789-00`, data `1990-05-15` (Joao Silva, score 750)
2. **Consulta de limite:** deve exibir R$ 5.000,00
3. **Aumento aprovado:** solicitar R$ 20.000 (score 750 -> limite maximo R$ 15.000)
4. **Score baixo:** CPF `222.333.444-55` (Pedro Alves, score 280) -> aumento rejeitado
5. **Entrevista de credito:** responder perguntas -> score recalculado
6. **Cambio:** perguntar cotacao do dolar (USD) e euro (EUR)

## Estrutura do Projeto

```
banco_agil/
+-- app.py                          # Interface Streamlit
+-- requirements.txt
+-- .env.example
+-- data/
|   +-- clientes.csv                # 10 clientes ficticios
|   +-- score_limite.csv            # Tabela score x limite
|   +-- solicitacoes_aumento_limite.csv  # Gerado em runtime
+-- src/
|   +-- state.py                    # BankState (TypedDict)
|   +-- graph.py                    # Grafo LangGraph
|   +-- agents/
|   |   +-- triagem.py
|   |   +-- credito.py
|   |   +-- entrevista_credito.py
|   |   +-- cambio.py
|   +-- tools/
|   |   +-- csv_tools.py
|   |   +-- auth_tools.py
|   |   +-- credit_tools.py
|   |   +-- exchange_tools.py
|   +-- utils/
|       +-- score_calculator.py
+-- tests/
    +-- test_auth.py
    +-- test_credit.py
    +-- test_score.py
    +-- test_graph.py
    +-- fixtures/
        +-- clientes_test.csv
        +-- score_limite_test.csv
```
