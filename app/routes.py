from fastapi import APIRouter
from app.models import TransactionSchema, BudgetSchema, MetaSchema
from app.services import (
    create_transaction, 
    list_transactions, 
    get_dashboard_summary,
    create_or_update_budget,
    list_budgets_with_progress,
    create_meta,
    list_metas,
    update_meta_valor,
    delete_meta_db,
    update_meta_completa
)

router = APIRouter()

# --- ROTAS DE TRANSAÇÃO ---
@router.post("/transactions/")
def add_transaction(transaction: TransactionSchema):
    return create_transaction(transaction)

@router.get("/transactions/")
def get_all_transaction():
    return list_transactions()

@router.get("/transactions/summary")
def summary():
    return get_dashboard_summary()

# --- ROTAS DE ORÇAMENTO ---
@router.post("/budgets/")
def add_budget(budget: BudgetSchema):
    return create_or_update_budget(budget)

@router.get("/budgets/")
def get_budgets():
    return list_budgets_with_progress()

# --- ROTAS DE METAS ---
@router.post("/metas/")
def add_meta(meta: MetaSchema):
    return create_meta(meta)

@router.get("/metas/")
def get_all_metas():
    return list_metas()

@router.put("/metas/{meta_id}/valor/")
def update_valor(meta_id: str, payload: dict):
    valor_guardado = payload.get("valor_guardado", 0.0)
    return {"sucesso": update_meta_valor(meta_id, valor_guardado)}

@router.delete("/metas/{meta_id}")
def remove_meta(meta_id: str):
    return {"sucess": delete_meta_db(meta_id)}

@router.put("/metas/{meta_id}")
def edit_meta(meta_id: str, meta: MetaSchema):
    return {"success": update_meta_completa(meta_id, meta)}
