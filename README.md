# Gerenciador Financeiro

Aplicação Full Stack para organizar finanças pessoais, com back-end em FastAPI, banco de dados MongoDB (Atlas ou local) e interface interativa em Streamlit.

## Funcionalidades principais

- **Autenticação:** cadastro e login; a interface valida CPF e e-mail, e a API armazena a senha como hash com salt.
- **Dashboard:** consulta de saldo, receitas, despesas e economia a partir das transações cadastradas.
- **Transações:** cadastro e listagem de receitas e despesas, com filtros por tipo e categoria na interface.
- **Orçamentos:** limites por categoria e acompanhamento dos gastos com barra de progresso. Os orçamentos mensais ficam apenas na sessão atual; os demais são salvos no banco.
- **Metas financeiras:** cadastro, listagem, edição e exclusão de metas, com aportes e retiradas do valor guardado.
- **Em desenvolvimento:** telas de Relatórios e Conversor de Moedas.

**Limitações atuais:** embora o dashboard exiba métricas identificadas como mensais, a API as calcula usando todas as transações, sem filtro por data. Os orçamentos salvos no banco também consideram todas as despesas da categoria, sem mês ou ano. A validação de formato de CPF e e-mail ocorre na interface, não na API. O login libera a interface, mas as rotas financeiras não validam o token nem separam os dados por usuário.

## Estrutura de pastas

```text
app/       API FastAPI, modelos, serviços e conexão com o MongoDB
frontend/  Interface Streamlit e comunicação com a API
```

## Requisitos

- Python instalado.
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

   A interface estará disponível normalmente em `http://localhost:8501`. Mantenha o back-end e o front-end em execução simultaneamente.

## Documentação interativa

Com a API em execução, acesse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para consultar e testar os endpoints no Swagger UI.

## Endpoints da API

| Módulo | Método | Caminho | Descrição |
| --- | --- | --- | --- |
| Geral | `GET` | `/` | Verifica se a API está em execução |
| Autenticação | `POST` | `/auth/register` | Cadastra um usuário |
| Autenticação | `POST` | `/auth/login` | Autentica um usuário |
| Transações | `POST` | `/transactions/` | Cadastra uma transação |
| Transações | `GET` | `/transactions/` | Lista as transações |
| Transações | `GET` | `/transactions/summary` | Retorna o resumo do dashboard |
| Orçamentos | `POST` | `/budgets/` | Cria ou atualiza o limite de uma categoria |
| Orçamentos | `GET` | `/budgets/` | Lista orçamentos com os gastos e o progresso |
| Metas | `POST` | `/metas/` | Cadastra uma meta |
| Metas | `GET` | `/metas/` | Lista as metas |
| Metas | `PUT` | `/metas/{meta_id}/valor/` | Atualiza o valor guardado |
| Metas | `PUT` | `/metas/{meta_id}` | Atualiza uma meta |
| Metas | `DELETE` | `/metas/{meta_id}` | Exclui uma meta |

A rota de atualização do valor é registrada com barra final; a versão sem barra (`/metas/{meta_id}/valor`) é redirecionada pela API.

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

O valor deve ser maior que zero; `data` é obrigatória e a interface usa o formato `YYYY-MM-DD`. Use `Receita` ou `Despesa` em `tipo`. `observacao` é opcional.

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

Para atualizar somente o valor guardado, envie `{"valor_guardado": 600.0}` para `PUT /metas/{meta_id}/valor/`. O valor enviado é o novo total, não o valor do aporte ou da retirada.

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

O nome deve ter pelo menos 2 caracteres e a senha, pelo menos 8. Para login, envie `email` e `senha` para `POST /auth/login`.

## Trabalhando em equipe com Git e GitHub

Os comandos devem ser executados no terminal, dentro da pasta do projeto. Antes de começar uma tarefa, atualize a `main` e crie uma branch própria para a funcionalidade ou teste:

```bash
git checkout main
git pull origin main
git checkout -b nome-da-feature
```

Após implementar e testar as alterações, registre e publique a branch:

```bash
git status
git add .
git commit -m "feat: descricao do que foi implementado"
git push -u origin nome-da-feature
```

Abra um pull request para revisão e merge na `main`. Antes de concluir, atualize sua branch com as mudanças mais recentes da `main` e resolva eventuais conflitos:

```bash
git checkout main
git pull origin main
git checkout nome-da-feature
git merge main
git push origin nome-da-feature
```

Combine com a outra pessoa quem trabalha em cada parte, evite alterações simultâneas nos mesmos arquivos e mantenha as branches pequenas e atualizadas. Depois do merge, atualize sua `main` local com `git pull origin main`.

Para consultar o histórico recente, use `git log --oneline`.
