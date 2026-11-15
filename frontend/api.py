import requests
import streamlit as st
API_URL = "http://127.0.0.1:8000"

def _headers_usuario():
    user_id = st.session_state.get("auth_user_id", "")
    return {"X-User-Id": str(user_id)}

# ---- Funções GET ----

def buscar_transacoes():
    try:
        response = requests.get(
            f"{API_URL}/transactions/",
            headers=_headers_usuario(),
            timeout=10
        )
        response.raise_for_status()
        dados = response.json()
        return dados if isinstance(dados, list) else None
    except (requests.RequestException, ValueError) as erro:
        print(f"Erro ao buscar transações: {erro}")
        return None

def buscar_resumo_dashboard():
    try:
        response = requests.get(
            f"{API_URL}/transactions/summary",
            headers=_headers_usuario(),
            timeout=5
        )
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

def buscar_orcamentos():
    try:
        response = requests.get(
            f"{API_URL}/budgets/",
            headers=_headers_usuario(),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Erro ao buscar orçamentos {e}")
        return []
# ---- Funções POST ----

def criar_transacao(payload):
    try:
        response = requests.post(
            f"{API_URL}/transactions/",
            json=payload,
            headers=_headers_usuario(),
            timeout=5
        )
        return response.status_code in [200, 201]
    except Exception:
        return False

def criar_orcamento(payload):
    try:
        response = requests.post(
            f"{API_URL}/budgets/",
            json=payload,
            headers=_headers_usuario(),
            timeout=5
        )
        return response.status_code in [200, 201]
    except Exception:
        return False

# ---- Funções de METAS ----

def buscar_metas():
    try:
        response = requests.get(
            f"{API_URL}/metas/",
            headers=_headers_usuario(),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Erro ao buscar metas: {e}")
        return []

def criar_meta(payload):
    try:
        response = requests.post(
            f"{API_URL}/metas/",
            json=payload,
            headers=_headers_usuario(),
            timeout=5
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Erro ao criar meta: {e}")
        return False

def atualizar_valor_meta(meta_id, valor_guardado):
    try:
        response = requests.put(
            f"{API_URL}/metas/{meta_id}/valor",
            json={"valor_guardado": valor_guardado},
            headers=_headers_usuario(), timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao atualizar valor da meta: {e}")
        return False

def editar_meta_api(meta_id, payload):
    try:
        response = requests.put(
            f"{API_URL}/metas/{meta_id}",
            json=payload,
            headers=_headers_usuario(),
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao editar meta: {e}")
        return False

def excluir_meta_api(meta_id):
    try:
        response = requests.delete(
            f"{API_URL}/metas/{meta_id}",
            headers=_headers_usuario(),
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao excluir meta: {e}")
        return False

# ---- Funções de RELATÓRIOS ----

def buscar_relatorio(data_inicio: str, data_fim: str):
    try:
        response = requests.get(
            f"{API_URL}/reports/",
            params={"data_inicio": data_inicio, "data_fim": data_fim},
            headers=_headers_usuario(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Erro ao buscar relatório: {e}")
        return None

def baixar_relatorio_excel(data_inicio: str, data_fim: str):
    try:
        response = requests.get(
            f"{API_URL}/reports/export/excel",
            params={"data_inicio": data_inicio, "data_fim": data_fim},
            headers=_headers_usuario(),
            timeout=10
        )
        return response.content if response.status_code == 200 else None
    except Exception:
        return None

def baixar_relatorio_pdf(data_inicio: str, data_fim: str):
    try:
        response = requests.get(
            f"{API_URL}/reports/export/pdf",
            params={"data_inicio": data_inicio, "data_fim": data_fim},
            headers=_headers_usuario(),
            timeout=10
        )
        return response.content if response.status_code == 200 else None
    except Exception:
        return None