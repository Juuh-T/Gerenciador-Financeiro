import requests

API_URL = "http://127.0.0.1:8000"

# ---- Funções GET ----

def buscar_transacoes():
    try:
        response = requests.get(f"{API_URL}/transactions/", timeout=10)
        response.raise_for_status()
        dados = response.json()
        return dados if isinstance(dados, list) else None
    except (requests.RequestException, ValueError) as erro:
        print(f"Erro ao buscar transações: {erro}")
        return None


# def buscar_transacoes():
#     try:
#         response = requests.get(f"{API_URL}/transactions/")
#         if response.status_code == 200:
#             return response.json()

#         else:
#             print(f"Erro na API: Status {response.status_code}")
#             return []

#     except Exception as e:
#         print(f"Erro ao buscar transações: {e}")
#     return []

def buscar_resumo_dashboard():
    try:
        response = requests.get(f"{API_URL}/transactions/summary")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {
        "saldo_atual": 0.0,
        "receita_mes": 0.0,
        "despesa_mes": 0.0,
        "economia_mes": 0.0
    }

# ---- Funções POST ----

def criar_transacao(payload):
    try:
        response = requests.post(f"{API_URL}/transactions/", json=payload)
        return response.status_code in [200, 201]
    except Exception:
        return False