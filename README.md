# Gerenciador Financeiro

API para cadastro e consulta de transações financeiras, desenvolvida com FastAPI e MongoDB.

## Requisitos

- Python instalado
- MongoDB em execução

Por padrão, a aplicação se conecta ao MongoDB local em `mongodb://localhost:27017`. Para usar outra instância, configure a variável de ambiente `MONGO_URI`.

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

4. Se necessário, defina `MONGO_URI` antes de iniciar a aplicação:

   **Windows (PowerShell):**

   ```powershell
   $env:MONGO_URI = "mongodb://localhost:27017"
   ```

   **Linux/macOS:**

   ```bash
   export MONGO_URI="mongodb://localhost:27017"
   ```

   A aplicação também carrega variáveis de um arquivo `.env` na pasta do projeto.

5. Inicie o servidor:

   ```bash
   uvicorn app.main:app --reload
   ```

O servidor ficará disponível em `http://127.0.0.1:8000`.

## Documentação interativa

Com o servidor em execução, acesse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para consultar e testar os endpoints pela interface do Swagger UI.

## Endpoints

| Método | Caminho | Descrição |
|---|---|---|
| `GET` | `/` | Verifica se a API está em execução |
| `POST` | `/transactions/` | Cadastra uma transação |
| `GET` | `/transactions/` | Lista as transações cadastradas |

Exemplo de corpo para cadastrar uma transação:

```json
{
  "tipo": "despesa",
  "valor": 45.9,
  "categoria": "alimentação",
  "descricao": "Almoço",
  "observacao": "Refeição durante a semana"
}
```

O campo `data` é opcional; quando omitido, a API preenche a data e hora atuais. O campo `valor` deve ser maior que zero. Os valores esperados para `tipo` são `receita` e `despesa`.

## Trabalhando em equipe com Git e GitHub

Os comandos abaixo devem ser executados no terminal, dentro da pasta do projeto. Os exemplos usam Bash (disponível, por exemplo, no Git Bash).

### Primeiro envio do projeto

Use estes comandos para inicializar o repositório local e enviar o projeto pela primeira vez. O repositório remoto deve estar vazio:

```bash
git init
git add .
git commit -m "feat: estrutura inicial do projeto e dependencias"
git branch -M main
git remote add origin https://github.com/Juuh-T/Gerenciador-Financeiro.git
git push -u origin main
```

### Clonar o projeto

Na primeira vez em outra máquina, clone o repositório e entre na pasta:

```bash
git clone https://github.com/Juuh-T/Gerenciador-Financeiro.git
cd Gerenciador-Financeiro
```

Depois, siga as instruções de [execução local](#como-executar-localmente) para configurar o ambiente e instalar as dependências.

### Rotina diária de trabalho

Depois de implementar e testar suas alterações, registre e envie seu trabalho. Antes de enviar, atualize sua branch com as mudanças que a outra pessoa publicou:

```bash
git add .
git commit -m "feat: descricao do que foi implementado"
git pull --rebase origin main
git push origin main
```

### Baixar as novidades

Se você não tem alterações locais pendentes e quer apenas atualizar sua cópia:

```bash
git pull origin main
```

### Comandos úteis

```bash
# Verifica o status dos arquivos
git status

# Mostra o histórico recente de commits
git log --oneline
```
