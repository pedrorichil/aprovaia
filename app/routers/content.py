from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from .. import crud, schemas, security, models, ai_services
from ..database import get_db

router = APIRouter(
    prefix="/content",
    tags=["Gerenciamento de Conteúdo"],
    dependencies=[Depends(security.get_current_active_user_with_role(models.UserRole.admin))]
)

@router.post("/questions/upload", response_model=schemas.Question)
def upload_question(question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    # 1. Gerar o embedding (vetor) do conteúdo da questão usando Gemini.
    embedding = ai_services.generate_embedding(text=question.content)
    if not embedding:
        raise HTTPException(status_code=500, detail="Falha ao gerar o embedding da questão com o serviço de IA.")

    # 2. Inserir o vetor e metadados no Banco Vetorial (ChromaDB/Pinecone).
    #    A API do banco vetorial retornaria um ID único.
    #    Simulação:
    vector_id = f"vec_{uuid.uuid4()}"
    # Em um caso real: vector_id = vector_db.upsert(vector=embedding, metadata={...})
    
    # 3. Salvar a questão no PostgreSQL com o vector_id.
    return crud.create_question(db=db, question=question, vector_id=vector_id)
