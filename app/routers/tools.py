from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, security, ai_services

router = APIRouter(
    prefix="/tools",
    tags=["Ferramentas de IA"],
    dependencies=[Depends(security.get_current_user)] # Protege todas as rotas neste router
)

@router.post("/grade-essay", response_model=schemas.EssayGradeResponse)
def grade_essay(request: schemas.EssayGradeRequest):
    """
    Recebe o texto de uma redação e um tema, e retorna uma correção detalhada
    baseada nos critérios do ENEM, gerada pela IA do Gemini.
    """
    if not request.essayText or not request.theme:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O tema e o texto da redação são obrigatórios."
        )

    correction = ai_services.grade_essay_with_gemini(
        essay_text=request.essayText,
        theme=request.theme
    )

    if not correction:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível corrigir a redação no momento. Tente novamente mais tarde."
        )

    return correction

@router.post("/ask-tutor", response_model=schemas.TutorResponse)
def ask_tutor(request: schemas.TutorRequest):
    """
    Recebe uma dúvida de um aluno e um contexto opcional, e retorna uma
    explicação gerada pelo tutor de IA.
    """
    answer = ai_services.ask_tutor_with_gemini(
        question=request.question,
        context=request.context
    )
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O tutor não está disponível no momento."
        )
    return {"answer": answer}

@router.post("/summarize-content", response_model=schemas.SummarizeResponse)
def summarize_content(request: schemas.SummarizeRequest):
    """
    Recebe um texto e retorna um resumo em bullet points gerado pela IA.
    """
    summary = ai_services.summarize_content_with_gemini(
        text_to_summarize=request.textToSummarize
    )
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível gerar o resumo."
        )
    return {"summary": summary}
