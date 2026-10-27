# Gerenciador-Financeiro


# Como rodar o projeto localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/Juuh-T/Gerenciador-Financeiro.git
cd Gerenciador-Financeiro
```

### 2. Criar e ativar o ambiente virtual

- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
- **Linux/Mac:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Executar o servidor

```bash
uvicorn app.main:app --reload
```
