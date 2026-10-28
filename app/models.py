from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TransactionSchema(BaseModel):
    tipo: str = Field(..., description="Deve ser 'receita' ou 'despesa'")
    valor: float = Field(..., gt=0, desption="O valor deve ser maior que zero")
    categoria: str
    descricao: str = None
    data: datetime = Field(default_factory=datetime.now)
    observacao: Optional[str] = None