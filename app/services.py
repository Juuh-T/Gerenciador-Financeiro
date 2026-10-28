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

