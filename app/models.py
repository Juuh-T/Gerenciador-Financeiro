from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class TransactionSchema(BaseModel):
    descricao: str = Field(..., min_length=1)
    valor: float = Field(..., gt=0)
    tipo: str # Receita ou Despesa
    categoria: str
    data: str
    observacao: Optional[str] = None

class BudgetSchema(BaseModel):
    categoria: str
    limite: float = Field(..., gt=0)