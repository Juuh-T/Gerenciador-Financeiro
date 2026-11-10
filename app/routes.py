from fastapi import APIRouter
from app.models import TransactionSchema, BudgetSchema
from app.services import (
    create_transaction, 
    list_transactions, 
    get_dashboard_summary,
    create_or_update_budget,
    list_budgets_with_progress
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