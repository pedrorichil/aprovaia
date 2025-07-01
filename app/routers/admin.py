from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
import uuid # <-- CORREÇÃO: Importar o módulo uuid
from .. import schemas, security, crud, models
from ..database import get_db
from ..tasks import process_exam_pdf
import shutil
import os

router = APIRouter(
    prefix="/admin",
    tags=["Administração"],
    dependencies=[Depends(security.get_current_active_user_with_role(models.UserRole.admin))]
)

@router.post("/exams/upload", response_model=schemas.ExamUploadResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_exam(
    contest: str = Form(...),
    year: int = Form(...),
    file: UploadFile = File(...),
):
    """
    Faz o upload de um ficheiro PDF de uma prova para processamento em segundo plano.
    """
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task = process_exam_pdf.delay(file_path, contest, year)

    return {
        "message": "Prova recebida e agendada para processamento.",
        "task_id": task.id
    }

@router.put("/questions/{question_id}/answer-key", response_model=schemas.AnswerKeyUpdateResponse)
def update_answer_key(
    question_id: UUID,
    data: schemas.QuestionAnswerKeyUpdate,
    db: Session = Depends(get_db)
):
    """Define ou atualiza a alternativa correta para uma questão."""
    updated_question = crud.update_Youtube_key(db, question_id, data.correct_option)
    if not updated_question:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    
    return {
        "id": updated_question.id,
        "correct_option": updated_question.correct_option,
        "message": "Gabarito atualizado com sucesso."
    }