from fastapi import APIRouter
from app.models import TransactionSchema
from app.services import create_transaction, list_transactions

router = APIRouter(prefix="/transactions", tags=["Transações"])

@router.post("/")
def add_transaction(transaction: TransactionSchema):
    return create_transaction(transaction)

@router.get("/")
def get_all_transaction():
    return list_transactions()

