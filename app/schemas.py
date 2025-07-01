from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import UserRole
import enum

class TenantBase(BaseModel):
    name: str
class TenantCreate(TenantBase):
    pass
class Tenant(TenantBase):
    id: UUID4
    created_at: datetime
    class Config:
        from_attributes = True

class ProfileBase(BaseModel):
    full_name: str
    current_goal: Optional[str] = None
class Profile(ProfileBase):
    id: UUID4
    user_id: UUID4
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole = UserRole.student
    tenant_name: str
class User(UserBase):
    id: UUID4
    role: UserRole
    tenant_id: UUID4
    profile: Profile
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    email: Optional[str] = None

class QuestionBase(BaseModel):
    content: str
    options: Dict[str, str]
    correct_option: str
    subject: str
    topic: str
    source: Optional[str] = None
class QuestionCreate(QuestionBase):
    pass
class Question(QuestionBase):
    id: UUID4
    vector_id: Optional[str] = None
    class Config:
        from_attributes = True

class StudentAnswerCreate(BaseModel):
    question_id: UUID4
    selected_option: str
    time_taken_ms: Optional[int] = None
class StudentAnswer(BaseModel):
    id: UUID4
    profile_id: UUID4
    question_id: UUID4
    selected_option: str
    is_correct: bool
    ai_analysis: Optional[Dict[str, Any]] = None
    answered_at: datetime
    class Config:
        from_attributes = True

class ProficiencyMap(BaseModel):
    topic: str
    proficiency_score: float
    last_updated: datetime
    class Config:
        from_attributes = True

class StudentProgress(BaseModel):
    profile: Profile
    proficiency_maps: List[ProficiencyMap]
class StudentSummary(StudentProgress):
    recent_answers: List[StudentAnswer]

class EssayGradeRequest(BaseModel):
    """Schema para a requisição de correção de redação."""
    essayText: str = Field(..., description="O texto completo da redação a ser avaliada.")
    theme: str = Field(..., description="O tema proposto para a redação.")

class EssayCriterionFeedback(BaseModel):
    """Schema para o feedback de um único critério do ENEM."""
    nome: str
    nota: int
    feedback: str

class EssayGradeResponse(BaseModel):
    """Schema para a resposta completa da correção da redação."""
    feedback_geral: str
    nota_total: int
    criterios: List[EssayCriterionFeedback]


# --- SCHEMAS PARA O CORRETOR DE REDAÇÃO ---

class EssayGradeRequest(BaseModel):
    essayText: str = Field(..., description="O texto completo da redação a ser avaliada.")
    theme: str = Field(..., description="O tema proposto para a redação.")

class EssayCriterionFeedback(BaseModel):
    nome: str
    nota: int
    feedback: str

class EssayGradeResponse(BaseModel):
    feedback_geral: str
    nota_total: int
    criterios: List[EssayCriterionFeedback]

# --- NOVOS SCHEMAS PARA ASSISTENTE TUTOR E RESUMIDOR ---

class TutorRequest(BaseModel):
    """Schema para a requisição ao assistente tutor."""
    question: str = Field(..., description="A dúvida do aluno.")
    context: Optional[str] = Field(None, description="Opcional. O material de estudo que o aluno está a ver.")

class TutorResponse(BaseModel):
    """Schema para a resposta do assistente tutor."""
    answer: str

class SummarizeRequest(BaseModel):
    """Schema para a requisição de resumo."""
    textToSummarize: str = Field(..., description="O texto a ser resumido.")

class SummarizeResponse(BaseModel):
    """Schema para a resposta do resumo."""
    summary: str

class ProficiencyLevel(str, enum.Enum):
    """Enum para os níveis de proficiência autoavaliados."""
    iniciante = "iniciante"
    intermediario = "intermediario"
    avancado = "avancado"

class OnboardingTopicProficiency(BaseModel):
    """Schema para a proficiência de um único tópico durante o onboarding."""
    topic: str = Field(..., description="O nome do tópico, ex: 'Análise Combinatória'")
    level: ProficiencyLevel = Field(..., description="O nível de conhecimento autoavaliado.")

class OnboardingRequest(BaseModel):
    """Schema para a requisição completa do processo de onboarding."""
    goal: str = Field(..., description="O objetivo principal do aluno, ex: 'ENEM'")
    proficiencies: List[OnboardingTopicProficiency] = Field(..., description="Lista das proficiências autoavaliadas.")

class OnboardingResponse(BaseModel):
    """Schema para a resposta de sucesso do onboarding."""
    message: str

class UserWithOnboardingStatus(User):
    """
    Estende o schema User para incluir um campo que informa
    se o processo de onboarding foi concluído.
    """
    has_completed_onboarding: bool

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User # Inclui o objeto do utilizador

class ExamUploadResponse(BaseModel):
    message: str
    task_id: str

class AnswerKeyUpdateResponse(BaseModel):
    id: UUID4
    correct_option: str
    message: str

class AnswerSubmissionResponse(BaseModel):
    answer_id: UUID4
    is_correct: bool
    correct_option: str

class AnswerAnalysisResponse(BaseModel):
    id: UUID4
    ai_analysis: Optional[Dict[str, Any]] = None

class DifficultTopic(BaseModel):
    topic: str
    average: float

class Engagement(BaseModel):
    active_students: int
    total_students: int

class TeacherDashboardResponse(BaseModel):
    class_average_score: float
    most_difficult_topics: List[DifficultTopic]
    engagement: Engagement

class TeacherStudentDetailResponse(BaseModel):
    profile: Profile
    proficiency_map: List[ProficiencyMap]
    recent_errors: List[StudentAnswer]

class QuestionAnswerKeyUpdate(BaseModel):
    correct_option: str