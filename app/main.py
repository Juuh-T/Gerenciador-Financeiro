from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as transaction_router

app = FastAPI(title="Gerenciador Financeiro API")

# Habilita CORS para permitir que o front-end faça requisições
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(transaction_router)

@app.get("/")
def home():
    return{"status": "API rodando"}