from app.database import get_database
from app.models import TransactionSchema

db = get_database()
collection = db["transactions"]

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
            receita_mes += val

    economia_mes = receita_mes - despesa_mes

    return {
        "saldo_atual": saldo_atual,
        "receita_mes": receita_mes,
        "despesa_mes": despesa_mes,
        "economia_mes": economia_mes
    }