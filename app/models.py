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

class MetaSchema(BaseModel):
    nome: str = Field(..., min_length=1)
    descricao: Optional[str] = ""
    valor_alvo: float = Field(..., gt=0)
    valor_guardado: float = Field(0.0, ge=0)
    prazo: str

class UserRegisterSchema(BaseModel):
    nome: str = Field(..., min_length=2)
    telefone: str
    cpf: str
    email: str
    data_nascimento: str
    senha: str = Field(..., min_length=8)

class UserLoginSchema(BaseModel):
    email: str
    senha: str