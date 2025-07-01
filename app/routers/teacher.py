from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import redis
from .. import schemas, security, crud, models
from ..database import get_db
from ..config import settings
import json

router = APIRouter(
    prefix="/teacher",
    tags=["Professor"],
    dependencies=[Depends(security.get_current_active_user_with_role(models.UserRole.teacher))]
)

try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except redis.exceptions.ConnectionError:
    redis_client = None

@router.get("/dashboard", response_model=schemas.TeacherDashboardResponse)
def get_teacher_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    teacher_id = str(current_user.profile.id)
    cache_key = f"dashboard:{teacher_id}"

    if redis_client:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

    dashboard_data = crud.get_teacher_dashboard_data(db, teacher_profile_id=current_user.profile.id)

    if redis_client:
        # Pydantic models need to be converted to dicts before JSON serialization
        # This assumes the CRUD function returns a dict, which it does.
        redis_client.set(cache_key, json.dumps(dashboard_data), ex=300)

    return dashboard_data

@router.get("/students/{student_id}", response_model=schemas.TeacherStudentDetailResponse)
def get_student_details(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Retorna o perfil detalhado e o progresso de um aluno específico."""
    student_profile = db.query(models.Profile).filter(models.Profile.id == student_id).first()
    if not student_profile or student_profile.user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Aluno não encontrado ou não pertence à sua organização.")

    student_data = crud.get_student_details_for_teacher(db, student_id=student_id)
    if not student_data:
        raise HTTPException(status_code=404, detail="Dados do aluno não encontrados.")
    
    return student_data