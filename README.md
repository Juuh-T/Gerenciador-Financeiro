# Gerenciador Financeiro

Aplicação Full Stack para organizar finanças pessoais, com back-end em FastAPI, banco de dados MongoDB (Atlas ou local) e interface interativa em Streamlit.

## Funcionalidades principais

- **Autenticação e isolamento de dados:** cadastro e login com validação de CPF e e-mail na interface; a API armazena a senha como hash PBKDF2-SHA256 com salt e isola transações, orçamentos, metas e relatórios por usuário autenticado (`X-User-Id`).
- **Dashboard:** consulta de saldo atual, receitas, despesas e economia a partir das transações cadastradas pelo usuário.
- **Transações:** cadastro e listagem de receitas e despesas, com filtros por tipo e categoria na interface.
- **Orçamentos:** definição de limites por categoria e acompanhamento dos gastos com barra de progresso e alertas visuais. Inclui controle persistente no banco e simulação mensal por sessão.
- **Metas financeiras:** cadastro, listagem, edição e exclusão de metas, com aportes e retiradas do valor guardado e acompanhamento de prazo.
- **Relatórios financeiros:** filtragem de transações por intervalo de datas, métricas consolidadas do período, gráfico comparativo de Receitas vs. Despesas e exportação da planilha em Excel (`.xlsx`) e PDF (`.pdf`).
- **Conversor de moedas:** conversão em tempo real entre Real (`BRL`), Dólar (`USD`) e Euro (`EUR`) utilizando cotações atualizadas da AwesomeAPI.

## Estrutura de pastas

```text
app/       API FastAPI, modelos Pydantic, regras de negócio e conexão com o MongoDB
frontend/  Interface Streamlit, autenticação e cliente HTTP para a API
```

## Requisitos

- Python 3.10 ou superior instalado.
- MongoDB local em execução ou uma instância MongoDB Atlas acessível.

## Como executar localmente

1. Clone o repositório e entre na pasta do projeto:

   ```bash
   git clone https://github.com/Juuh-T/Gerenciador-Financeiro.git
   cd Gerenciador-Financeiro
   ```

2. Crie e ative um ambiente virtual:

   **Windows (PowerShell):**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **Linux/macOS:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure a conexão com o banco em um arquivo `.env` na raiz do projeto:

   ```env
   MONGO_URI=mongodb://localhost:27017
   ```

   Para usar o MongoDB Atlas, substitua o valor pela URI da sua instância. Sem `MONGO_URI`, a aplicação usa o endereço local acima. Não compartilhe nem versione credenciais.

5. Inicie o back-end:

   ```bash
   uvicorn app.main:app --reload
   ```

   A API estará disponível em `http://127.0.0.1:8000`.

6. Em outro terminal, com o ambiente virtual ativado, inicie o front-end:

   ```bash
   python -m streamlit run frontend/app.py
   ```

   A interface estará disponível em `http://localhost:8501`. Mantenha o back-end e o front-end em execução simultaneamente.

## Documentação interativa

Com a API em execução, acesse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para consultar e testar os endpoints no Swagger UI.

## Endpoints da API

| Módulo | Método | Caminho | Descrição |
| --- | --- | --- | --- |
| Geral | `GET` | `/` | Verifica se a API está em execução |
| Autenticação | `POST` | `/auth/register` | Cadastra um usuário |
| Autenticação | `POST` | `/auth/login` | Autentica um usuário e retorna token e ID |
| Transações | `POST` | `/transactions/` | Cadastra uma transação do usuário |
| Transações | `GET` | `/transactions/` | Lista as transações do usuário |
| Transações | `GET` | `/transactions/summary` | Retorna o resumo financeiro do dashboard |
| Orçamentos | `POST` | `/budgets/` | Cria ou atualiza o limite de uma categoria |
| Orçamentos | `GET` | `/budgets/` | Lista orçamentos com os gastos e o progresso |
| Metas | `POST` | `/metas/` | Cadastra uma meta financeira |
| Metas | `GET` | `/metas/` | Lista as metas do usuário |
| Metas | `PUT` | `/metas/{meta_id}/valor` | Atualiza o valor guardado na meta |
| Metas | `PUT` | `/metas/{meta_id}` | Atualiza os dados de uma meta |
| Metas | `DELETE` | `/metas/{meta_id}` | Exclui uma meta |
| Relatórios | `GET` | `/reports/` | Retorna resumo, gráfico e transações por período |
| Relatórios | `GET` | `/reports/export/excel` | Exporta o relatório filtrado em `.xlsx` |
| Relatórios | `GET` | `/reports/export/pdf` | Exporta o relatório filtrado em `.pdf` |

*(As rotas autenticadas recebem o identificador do usuário logado através do cabeçalho HTTP `X-User-Id`.)*

### Exemplos de payload

**Transação** (`POST /transactions/`):

```json
{
  "descricao": "Almoço",
  "valor": 45.9,
  "tipo": "Despesa",
  "categoria": "Alimentação",
  "data": "2026-11-12",
  "observacao": "Refeição durante a semana"
}
```

**Orçamento** (`POST /budgets/`):

```json
{
  "categoria": "Alimentação",
  "limite": 500.0
}
```

**Meta** (`POST /metas/` ou `PUT /metas/{meta_id}`):

```json
{
  "nome": "Reserva de emergência",
  "descricao": "Reserva para imprevistos",
  "valor_alvo": 5000.0,
  "valor_guardado": 500.0,
  "prazo": "2027-12-31"
}
```

**Cadastro de usuário** (`POST /auth/register`):

```json
{
  "nome": "Maria Silva",
  "telefone": "11999999999",
  "cpf": "52998224725",
  "email": "maria@example.com",
  "data_nascimento": "1990-01-01",
  "senha": "senha-exemplo"
}
```