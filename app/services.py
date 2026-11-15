import io
import pandas as pd
from fpdf import FPDF
from fastapi.responses import StreamingResponse
import hashlib
import secrets
from fastapi import HTTPException
from app.database import get_database
from bson import ObjectId
from app.models import (
    TransactionSchema,
    BudgetSchema,
    MetaSchema,
    UserRegisterSchema,
    UserLoginSchema
    )

# ------ Lógica de Autenticação ------

def _gerar_hash_senha(senha: str, salt: str = None) -> str:
    if not salt:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${hash_obj.hex()}"

def _verificar_senha(senha_digitada: str, senha_salva: str) -> bool:
    try:
        salt, _ = senha_salva.split("$")
        return _gerar_hash_senha(senha_digitada, salt) == senha_salva
    except ValueError:
        return False

def register_user(data: UserRegisterSchema):
    if user_collection.find_one({"$or": [{"email": data.email.lower()}, {"cpf": data.cpf}]}):
        raise HTTPException(status_code = 409, detail = "Já existe uma conta com esse e-mail ou CPF")

    user_dict = data.model_dump()
    user_dict["email"] = data.email.lower().strip()
    user_dict["senha"] = _gerar_hash_senha(data.senha)

    result = user_collection.insert_one(user_dict)
    return {"id": str(result.inserted_id), "mensagem": "Usuário cadastrado com sucesso"}

def login_user(data: UserLoginSchema):
    user = user_collection.find_one({"email": data.email.lower().strip()})

    if not user or not _verificar_senha(data.senha, user["senha"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")  

    token = secrets.token_urlsafe(32)
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": str(user["_id"]),
            "nome": user["nome"],
            "email": user["email"]
        }
    }

# ------ Conexão Banco de Dados ------

db = get_database()
collection = db["transactions"]
budgets_collection = db["budgets"]
metas_collection = db["metas"]
user_collection = db["users"]

# ------ Validar Usuário ------

def _validar_user_id(user_id: str):
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=401, detail="Usuario não identificado na requisição")
    return user_id.strip()

# ------ Lógica Transação ------

def create_transaction(data: TransactionSchema, user_id: str):
    uid = _validar_user_id(user_id)
    transaction_dict = data.model_dump()
    transaction_dict["user_id"] = uid
    result = collection.insert_one(transaction_dict)
    transaction_dict["_id"] = str(result.inserted_id)
    return transaction_dict

def list_transactions(user_id: str):
    uid = _validar_user_id(user_id)
    transactions = list(collection.find({"user_id": uid}))
    for item in transactions:
        item["_id"] = str(item["_id"])
    return transactions

def get_dashboard_summary(user_id: str):
    uid = _validar_user_id(user_id)
    transactions = list(collection.find({"user_id": uid}))
    receitas = sum(float(t.get("valor", 0)) for t in transactions if str(t.get("tipo", "")). lower() == "receita")
    despesas = sum(float(t.get("valor", 0)) for t in transactions if str(t.get("tipo", "")). lower() == "despesa")
    saldo = receitas - despesas
    return {
        "saldo_atual": saldo,
        "receita_mes": receitas,
        "despesa_mes": despesas,
        "economia_mes": saldo
    }

# ------ Lógica Orçamento ------

def create_or_update_budget(data: BudgetSchema, user_id: str):
    uid = _validar_user_id(user_id)
    budgets_collection.update_one(
        {"user_id": uid, "categoria": data.categoria},
        {"$set": {"user_id": uid, "categoria": data.categoria, "limite": data.limite}},
        upsert=True
    )
    return {"categoria": data.categoria, "limite": data.limite}

def list_budgets_with_progress(user_id: str):
    uid = _validar_user_id(user_id)
    budgets = list(budgets_collection.find({"user_id": uid}))
    transactions = list(collection.find({"user_id": uid}))

    gastos_por_categoria = {}
    for t in transactions:
        cat = t.get("categoria")
        val = float(t.get("valor", 0))
        if cat and str(t.get("tipo", "")).lower() == "despesa":
            gastos_por_categoria[cat] = gastos_por_categoria.get(cat, 0.0) + val

    resultado = []
    for b in budgets:
        cat = b.get("categoria")
        limite = float(b.get("limite", 0.0))
        gasto_atual = gastos_por_categoria.get(cat, 0.0)

        resultado.append({
            "_id": str(b["_id"]),
            "categoria": cat,
            "limite": limite,
            "gasto_atual": gasto_atual,
            "disponivel": max(0.0, limite - gasto_atual),
            "percentual": min(1.0, gasto_atual / limite) if limite > 0 else 0.0
        })

    return resultado

# ------ Lógica de Metas ------

def create_meta(data: MetaSchema, user_id: str):
    uid = _validar_user_id(user_id)
    meta_dict = data.model_dump()
    meta_dict["user_id"] = uid
    result = metas_collection.insert_one(meta_dict)
    meta_dict["_id"] = str(result.inserted_id)
    return meta_dict

def list_metas(user_id: str):
    uid = _validar_user_id(user_id)
    metas = list(metas_collection.find({"user_id": uid}))
    for item in metas:
        item["_id"] = str(item["_id"])
    return metas

def update_meta_valor(meta_id: str, valor_guardado: float, user_id: str):
    uid = _validar_user_id(user_id)
    metas_collection.update_one(
        {"_id": ObjectId(meta_id), "user_id": uid},
        {"$set": {"valor_guardado": valor_guardado}}
    )
    return True

def delete_meta_db(meta_id: str, user_id: str):
    uid = _validar_user_id(user_id)
    metas_collection.delete_one({"_id": ObjectId(meta_id), "user_id": uid})
    return True

def update_meta_completa(meta_id: str, data: MetaSchema, user_id: str):
    uid = _validar_user_id(user_id)
    meta_dict = data.model_dump()
    meta_dict["user_id"] = uid
    metas_collection.update_one(
        {"_id": ObjectId(meta_id), "user_id": uid},
        {"$set": meta_dict}
    )
    return True

# ----- Lógica de relatórios -----

def _filtrar_transacoes_periodo(user_id: str, data_inicio: str, data_fim: str):
    uid = _validar_user_id(user_id)
    query = {
        "user_id": uid,
        "data": {"$gte": data_inicio, "$lte": data_fim}
    }
    transacoes = list(collection.find(query).sort("data", 1))
    for t in transacoes:
        t["_id"] = str(t["_id"])
    return transacoes

def get_relatorio_periodo(user_id: str, data_inicio: str, data_fim: str):
    transacoes = _filtrar_transacoes_periodo(user_id, data_inicio, data_fim)

    total_receitas = sum(
        float(t.get("valor", 0)) for t in transacoes if str(t.get("tipo", "")).lower() == "receita"
    )
    total_despesas = sum(
        float(t.get("valor", 0)) for t in transacoes if str(t.get("tipo", "")).lower() == "despesa"
        )

    agrupado = {}
    for t in transacoes:
        dt = str(t.get("data", "")).strip()
        tipo = str(t.get("tipo", "")).strip().lower()
        valor = float(t.get("valor", 0))
        if dt not in agrupado:
            agrupado[dt] = {"data": dt, "Receita": 0.0, "Despesa": 0.0}
        if tipo == "receita":
            agrupado[dt]["Receita"] += valor
        elif tipo == "despesa":
            agrupado[dt]["Despesa"] += valor

    return {
        "resumo": {
            "total_receitas": total_receitas,
            "total_despesas": total_despesas,
            "saldo_periodo": total_receitas - total_despesas
        },
        "grafico": list(agrupado.values()),
        "transacoes": transacoes
    }

def exportar_relatorio_excel(user_id: str, data_inicio: str, data_fim: str):
    transacoes = _filtrar_transacoes_periodo(user_id, data_inicio, data_fim)

    if transacoes:
        df = pd.DataFrame(transacoes)
        colunas = [c for c in [
            "data",
            "tipo",
            "categoria",
            "descricao",
            "valor",
            "observacao"
        ] if c in df.columns]
        df = df[colunas]
        df.columns = [c.capitalize() for c in df.columns]
    else:
        df = pd.DataFrame(columns=["Data", "Tipo", "Categoria", "Descricao", "Valor", "Observacao"])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatorio_Financeiro")
    buffer.seek(0)

    headers = {
        "Content-Disposition": f'attachment; filename="relatorio Financeiro de {data_inicio} a {data_fim}.xlsx"'
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

def exportar_relatorio_pdf(user_id: str, data_inicio: str, data_fim: str):
    dados = get_relatorio_periodo(user_id, data_inicio, data_fim)
    transacoes = dados["transacoes"]
    resumo = dados["resumo"]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatorio Financeiro", ln=True, align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Periodo: {data_inicio} ate {data_fim}", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Total Receitas: R$ {resumo['total_receitas']:.2f}  |  Total Despesas: R$ {resumo['total_despesas']:.2f}  |  Saldo: R$ {resumo['saldo_periodo']:.2f}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(28, 8, "Data", border=1)
    pdf.cell(24, 8, "Tipo", border=1)
    pdf.cell(35, 8, "Categoria", border=1)
    pdf.cell(73, 8, "Descricao", border=1)
    pdf.cell(30, 8, "Valor (R$)", border=1, ln=True)

    pdf.set_font("Helvetica", "", 9)
    for t in transacoes:
        desc = str(t.get("descricao", ""))[:35]
        cat = str(t.get("categoria", ""))[:18]
        pdf.cell(28, 7, str(t.get("data", "")), border=1)
        pdf.cell(24, 7, str(t.get("tipo", "")).encode("latin-1", "replace").decode("latin-1"), border=1)
        pdf.cell(35, 7, cat.encode("latin-1", "replace").decode("latin-1"), border=1)
        pdf.cell(73, 7, desc.encode("latin-1", "replace").decode("latin-1"), border=1)
        pdf.cell(30, 7, f"{float(t.get('valor', 0)):.2f}", border=1, align="R", ln=True)

    pdf_bytes = bytes(pdf.output())
    buffer = io.BytesIO(pdf_bytes)
    headers = {
        "Content-Disposition": f'attachment; filename="relatorio_{data_inicio}_a_{data_fim}.pdf"'
    }
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)