from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .. import crud, models, schemas, security
from ..database import get_db
from ..tasks import analyze_student_answer
from uuid import UUID

router = APIRouter(
    prefix="/student",
    tags=["Interface do Aluno"],
    dependencies=[Depends(security.get_current_active_user_with_role(models.UserRole.student))]
)

@router.get("/me", response_model=schemas.User)
def read_student_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user

@router.get("/progress", response_model=schemas.StudentProgress)
def read_student_progress(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    profile = current_user.profile
    proficiency_maps = crud.get_student_proficiency_maps(db, profile_id=profile.id)
    return {"profile": profile, "proficiency_maps": proficiency_maps}

@router.get("/assessment/next-question", response_model=schemas.Question)
def get_next_question(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    next_question = crud.get_next_question_for_student(db, profile_id=current_user.profile.id)
    if not next_question:
        raise HTTPException(status_code=404, detail="Parabéns! Nenhuma questão nova encontrada para você no momento.")
    return next_question

@router.post("/assessment/answer", response_model=schemas.AnswerSubmissionResponse)
def submit_answer(
    answer_data: schemas.StudentAnswerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    question = crud.get_question(db, question_id=answer_data.question_id)
    # ... (validação)
    
    is_correct = (question.correct_option == answer_data.selected_option)
    db_answer = crud.create_student_answer(db, profile_id=current_user.profile.id, answer=answer_data, is_correct=is_correct)

    # Dispara a tarefa Celery em vez de BackgroundTasks
    analyze_student_answer.delay(str(db_answer.id))

    return {
        "answer_id": db_answer.id,
        "is_correct": is_correct,
        "correct_option": question.correct_option
    }

@router.get("/answers/{answer_id}/analysis", response_model=schemas.AnswerAnalysisResponse)
def get_answer_analysis(
    answer_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Busca a análise de IA para uma resposta, garantindo que o aluno só pode ver as suas próprias."""
    answer = db.query(models.StudentAnswer).filter_by(id=answer_id).first()
    
    if not answer:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    
    if answer.profile_id != current_user.profile.id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado a esta análise.")
    
    return {"id": answer.id, "ai_analysis": answer.ai_analysis}
