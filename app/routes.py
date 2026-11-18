from fastapi import APIRouter, Header
from app.models import (
    TransactionSchema, 
    BudgetSchema, 
    MetaSchema, 
    UserRegisterSchema, 
    UserLoginSchema
)
from app.services import (
    create_transaction, 
    list_transactions, 
    get_dashboard_summary,
    create_or_update_budget,
    list_budgets_with_progress,
    delete_budget,
    create_meta,
    list_metas,
    update_meta_valor,
    update_meta_completa,
    delete_meta_db,
    register_user,
    login_user,
    get_relatorio_periodo,
    exportar_relatorio_excel,
    exportar_relatorio_pdf,
    update_transaction,
    delete_transaction
)

router = APIRouter()

# --- ROTAS DE TRANSAÇÃO ---
@router.post("/transactions/")
def add_transaction(transaction: TransactionSchema, x_user_id: str = Header(default="")):
    return create_transaction(transaction, x_user_id)

@router.get("/transactions/")
def get_transaction(x_user_id: str = Header(default="")):
    return list_transactions(x_user_id)

@router.get("/transactions/summary")
def get_summary(x_user_id: str = Header(default="")):
    return get_dashboard_summary(x_user_id)

@router.put("/transactions/{transaction_id}")
def edit_transaction(transaction_id: str, transaction: TransactionSchema, x_user_id: str = Header(default="")):
    return {"sucesso": update_transaction(transaction_id, transaction, x_user_id)}

@router.delete("/transactions/{transaction_id}")
def remove_transaction(transaction_id: str, x_user_id: str = Header(default="")):
    return {"sucesso": delete_transaction(transaction_id, x_user_id)}

# --- ROTAS DE ORÇAMENTO ---
@router.post("/budgets/")
def add_budget(budget: BudgetSchema, x_user_id: str = Header(default="")):
    return create_or_update_budget(budget, x_user_id)

@router.get("/budgets/")
def get_budgets(x_user_id: str = Header(default="")):
    return list_budgets_with_progress(x_user_id)

@router.delete("/budgets/{budget_id}")
def remove_budget(budget_id: str, x_user_id: str = Header(default="")):
    return {"sucesso": delete_budget(budget_id, x_user_id)}

# --- ROTAS DE METAS ---
@router.post("/metas/")
def add_meta(meta: MetaSchema, x_user_id: str = Header(default="")):
    return create_meta(meta, x_user_id)

@router.get("/metas/")
def get_all_metas(x_user_id: str = Header(default="")):
    return list_metas(x_user_id)

@router.put("/metas/{meta_id}/valor")
def update_valor_meta(meta_id: str, body: dict, x_user_id: str = Header(default="")):
    return {"sucesso": update_meta_valor(meta_id, body.get("valor_guardado", 0.0), x_user_id)}

@router.put("/metas/{meta_id}")
def edit_meta(meta_id: str, meta: MetaSchema, x_user_id: str = Header(default="")):
    return {"sucesso": update_meta_completa(meta_id, meta, x_user_id)}

@router.delete("/metas/{meta_id}")
def remove_meta(meta_id: str, x_user_id: str = Header(default="")):
    return {"sucesso": delete_meta_db(meta_id, x_user_id)}

# --- ROTAS DE AUTENTICAÇÃO ---
@router.post("/auth/register", status_code=201)
def register(user: UserRegisterSchema):
    return register_user(user)

@router.post("/auth/login")
def login(credentials: UserLoginSchema):
    return login_user(credentials)

# --- ROTAS DE RELATÓRIOS ---
@router.get("/reports/")
def get_report(data_inicio: str, data_fim: str, x_user_id: str = Header(default="")):
    return get_relatorio_periodo(x_user_id, data_inicio, data_fim)

@router.get("/reports/export/excel")
def download_report_excel(data_inicio: str, data_fim: str, x_user_id: str = Header(default="")):
    return exportar_relatorio_excel(x_user_id, data_inicio, data_fim)

@router.get("/reports/export/pdf")
def download_report_pdf(data_inicio: str, data_fim: str, x_user_id: str = Header(default="")):
    return exportar_relatorio_pdf(x_user_id, data_inicio, data_fim)