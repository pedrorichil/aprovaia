from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from app.database import engine
from app.routers import auth, student, teacher, content, tools, onboarding, admin

# 1. Criação das tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

# 2. Instanciação ÚNICA do FastAPI com os metadados
app = FastAPI(
    title="Plataforma de Estudo Adaptativo com Gemini",
    description="API para gerenciar alunos, questões e aprendizado com a IA do Google Gemini.",
    version="2.0.0"
)

# 3. Definição das origens permitidas para o CORS
origins = [
    "http://localhost:3000",  # A origem do seu app React
]

# 4. Aplicação do Middleware CORS na instância correta do app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# 5. Inclusão dos roteadores da aplicação
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(content.router)
app.include_router(tools.router)
app.include_router(onboarding.router)
app.include_router(admin.router)

# 6. Definição da rota principal
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bem-vindo à API da Plataforma de Estudo Adaptativo v2 com Gemini!"}