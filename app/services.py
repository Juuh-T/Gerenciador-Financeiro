from app.database import get_database
from app.models import TransactionSchema, BudgetSchema

#------ conexão banco de dados ------

db = get_database()
collection = db["transactions"]
budgets_collection = db["budgets"]

#------ Lógica Transação ------

def create_transaction(data: TransactionSchema):
    transaction_dict = data.model_dump()
    result = collection.insert_one(transaction_dict)
    transaction_dict["_id"] = str(result.inserted_id)
    return transaction_dict

def list_transactions():
    transactions = list(collection.find())
    for item in transactions:
        item["_id"] = str(item["_id"])
    return transactions

def get_dashboard_summary():
    transactions = list(collection.find())

    saldo_atual = 0.0
    receita_mes = 0.0
    despesa_mes = 0.0

    for t in transactions:
        val = float(t.get("valor", 0))
        if t.get("tipo") == "Receita":
            saldo_atual += val
            receita_mes += val
        elif t.get("tipo") == "Despesa":
            saldo_atual -= val
            despesa_mes += val #<-- arrumado agr

    economia_mes = receita_mes - despesa_mes

    return {
        "saldo_atual": saldo_atual,
        "receita_mes": receita_mes,
        "despesa_mes": despesa_mes,
        "economia_mes": economia_mes
    }

#------ Lógica Orçamento ------

def create_or_update_budget(data: BudgetSchema):
    budget_dict = data.model_dump()
    result = budgets_collection.update_one(
        {"categoria": data.categoria},
        {"$set": budget_dict},
        upsert = True
    )
    return budget_dict

def list_budgets_with_progress():
    budgets = list(budgets_collection.find())
    transactions = list(collection.find({"tipo": "Despesa"}))

    gastos_por_categoria = {}
    for t in transactions:
        cat = t.get("categoria")
        val = float(t.get("valor", 0))
        gastos_por_categoria[cat] = gastos_por_categoria.get(cat, 0.0) + val

    resultado = []
    for b in budgets:
        cat = t.get("categoria")
        limite = float(t.get("limite", 0.0))
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