from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, security, crud, models
from ..database import get_db

router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
    dependencies=[Depends(security.get_current_user)] # Protege o endpoint
)

@router.post("/complete", response_model=schemas.OnboardingResponse, status_code=status.HTTP_200_OK)
def complete_user_onboarding(
    onboarding_data: schemas.OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Endpoint final do processo de onboarding.
    Recebe o objetivo e as proficiências iniciais do utilizador e guarda no sistema.
    """
    crud.complete_onboarding(db=db, user=current_user, onboarding_data=onboarding_data)
    
    return {"message": "Onboarding concluído com sucesso! O seu plano de estudos foi iniciado."}