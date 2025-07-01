from sqlalchemy.orm import Session
from uuid import UUID
import random
from . import models, schemas, security, ai_services
from sqlalchemy import func, Float

# --- CRUD de Tenant ---
def get_tenant_by_name(db: Session, name: str) -> models.Tenant | None:
    return db.query(models.Tenant).filter(models.Tenant.name == name).first()

def create_tenant(db: Session, tenant: schemas.TenantCreate) -> models.Tenant:
    db_tenant = models.Tenant(name=tenant.name)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

# --- CRUD de User ---
def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    tenant = get_tenant_by_name(db, name=user.tenant_name)
    if not tenant:
        tenant = create_tenant(db, tenant=schemas.TenantCreate(name=user.tenant_name))

    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        tenant_id=tenant.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_profile = models.Profile(full_name=user.full_name, user_id=db_user.id)
    db.add(db_profile)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- CRUD de Question ---
def create_question(db: Session, question: schemas.QuestionCreate, vector_id: str) -> models.Question:
    db_question = models.Question(**question.model_dump(), vector_id=vector_id)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_question(db: Session, question_id: UUID) -> models.Question | None:
    return db.query(models.Question).filter(models.Question.id == question_id).first()

# --- CRUD de Respostas e Proficiência ---
def create_student_answer(db: Session, profile_id: UUID, answer: schemas.StudentAnswerCreate, is_correct: bool) -> models.StudentAnswer:
    db_answer = models.StudentAnswer(
        **answer.model_dump(),
        profile_id=profile_id,
        is_correct=is_correct
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def get_student_proficiency_maps(db: Session, profile_id: UUID) -> list[models.StudentProficiencyMap]:
    return db.query(models.StudentProficiencyMap).filter(models.StudentProficiencyMap.profile_id == profile_id).all()

def get_student_answers(db: Session, profile_id: UUID, limit: int = 10) -> list[models.StudentAnswer]:
    return db.query(models.StudentAnswer).filter(models.StudentAnswer.profile_id == profile_id).order_by(models.StudentAnswer.answered_at.desc()).limit(limit).all()

# --- LÓGICA DE NEGÓCIO PRINCIPAL ---

def get_next_question_for_student(db: Session, profile_id: UUID) -> models.Question | None:
    prof_maps = get_student_proficiency_maps(db, profile_id)
    target_topic = None
    if prof_maps:
        if random.random() < 0.8:
            prof_maps.sort(key=lambda x: x.proficiency_score)
            target_topic = prof_maps[0].topic
        else:
            target_topic = random.choice(prof_maps).topic

    if not target_topic:
        all_topics = db.query(models.Question.topic).distinct().all()
        if not all_topics: return None
        target_topic = random.choice(all_topics)[0]

    answered_q_ids = [ans.question_id for ans in get_student_answers(db, profile_id, limit=1000)]
    
    next_question = db.query(models.Question).filter(
        models.Question.topic == target_topic,
        models.Question.id.notin_(answered_q_ids)
    ).first()

    if not next_question:
        next_question = db.query(models.Question).filter(
            models.Question.id.notin_(answered_q_ids)
        ).first()

    return next_question

def analyze_answer_and_update_proficiency(db: Session, answer: models.StudentAnswer):
    """
    Função em background que chama o Gemini para análise e depois atualiza a proficiência.
    """
    if not answer.is_correct:
        # Chama o serviço de IA do Gemini para analisar o erro
        question_schema = schemas.Question.from_orm(answer.question)
        ai_analysis_result = ai_services.analyze_student_error(
            question=question_schema,
            student_answer=answer.selected_option
        )
        answer.ai_analysis = ai_analysis_result
        db.commit()

    # Atualiza o mapa de proficiência
    topic = answer.question.topic
    proficiency_map = db.query(models.StudentProficiencyMap).filter_by(profile_id=answer.profile_id, topic=topic).first()
    
    if not proficiency_map:
        proficiency_map = models.StudentProficiencyMap(profile_id=answer.profile_id, topic=topic, proficiency_score=0.0)
        db.add(proficiency_map)

    current_score = proficiency_map.proficiency_score
    result_value = 1.0 if answer.is_correct else 0.2
    new_score = (current_score * 4 + result_value) / 5
    
    proficiency_map.proficiency_score = new_score
    db.commit()

def has_proficiency_maps(db: Session, profile_id: UUID) -> bool:
    """
    Verifica de forma eficiente se existem entradas no mapa de proficiência
    para um determinado perfil. Retorna True se pelo menos uma existir.
    """
    return db.query(models.StudentProficiencyMap).filter(models.StudentProficiencyMap.profile_id == profile_id).first() is not None

def complete_onboarding(db: Session, user: models.User, onboarding_data: schemas.OnboardingRequest):
    # (Lógica existente para completar o onboarding, sem alterações)
    LEVEL_TO_SCORE = {
        schemas.ProficiencyLevel.iniciante: 0.2,
        schemas.ProficiencyLevel.intermediario: 0.5,
        schemas.ProficiencyLevel.avancado: 0.8,
    }
    profile = user.profile
    if profile:
        profile.current_goal = onboarding_data.goal
        db.add(profile)

    new_proficiency_maps = []
    for prof in onboarding_data.proficiencies:
        score = LEVEL_TO_SCORE.get(prof.level, 0.5)
        existing_map = db.query(models.StudentProficiencyMap).filter_by(
            profile_id=profile.id,
            topic=prof.topic
        ).first()
        if not existing_map:
            new_map_entry = models.StudentProficiencyMap(
                profile_id=profile.id,
                topic=prof.topic,
                proficiency_score=score
            )
            new_proficiency_maps.append(new_map_entry)
    if new_proficiency_maps:
        db.add_all(new_proficiency_maps)
    db.commit()

def update_question_vector_id(db: Session, question_id: UUID, vector_id: str) -> models.Question:
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question:
        db_question.vector_id = vector_id
        db.commit()
        db.refresh(db_question)
    return db_question

def update_Youtube_key(db: Session, question_id: UUID, correct_option: str) -> models.Question | None:
    """Atualiza o gabarito de uma questão."""
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question:
        db_question.correct_option = correct_option
        db.commit()
        db.refresh(db_question)
    return db_question

def get_teacher_dashboard_data(db: Session, teacher_profile_id: UUID):
    """Executa as queries de agregação reais para o painel do professor."""
    
    teacher = db.query(models.Profile).filter(models.Profile.id == teacher_profile_id).first()
    student_profiles = db.query(models.Profile).join(models.User).filter(
        models.User.tenant_id == teacher.user.tenant_id,
        models.User.role == 'student'
    ).all()
    student_profile_ids = [p.id for p in student_profiles]

    if not student_profile_ids:
        return {"class_average_score": 0, "most_difficult_topics": [], "engagement": {"active_students": 0, "total_students": 0}}

    avg_score_result = db.query(func.avg(models.StudentAnswer.is_correct.cast(Float))).filter(models.StudentAnswer.profile_id.in_(student_profile_ids)).scalar() or 0

    most_difficult_topics = db.query(
        models.StudentProficiencyMap.topic,
        func.avg(models.StudentProficiencyMap.proficiency_score).label('average_score')
    ).filter(models.StudentProficiencyMap.profile_id.in_(student_profile_ids))\
    .group_by(models.StudentProficiencyMap.topic)\
    .order_by('average_score')\
    .limit(3).all()

    difficult_topics_data = [{"topic": topic, "average": round(avg, 2)} for topic, avg in most_difficult_topics]

    return {
        "class_average_score": round(avg_score_result, 2),
        "most_difficult_topics": difficult_topics_data,
        "engagement": {
            "active_students": len(student_profile_ids),
            "total_students": len(student_profile_ids)
        }
    }

def get_student_details_for_teacher(db: Session, student_id: UUID):
    """Busca os detalhes de um aluno para o professor."""
    profile = db.query(models.Profile).filter(models.Profile.id == student_id).first()
    if not profile: return None

    proficiency_map = db.query(models.StudentProficiencyMap).filter_by(profile_id=student_id).order_by(models.StudentProficiencyMap.proficiency_score.desc()).all()
    recent_errors = db.query(models.StudentAnswer).filter_by(profile_id=student_id, is_correct=False).order_by(models.StudentAnswer.answered_at.desc()).limit(5).all()

    return {
        "profile": profile,
        "proficiency_map": proficiency_map,
        "recent_errors": recent_errors
    }

def update_question_answer_key(db: Session, question_id: UUID, correct_option: str) -> models.Question | None:
    """Atualiza o gabarito de uma questão."""
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question:
        db_question.correct_option = correct_option
        db.commit()
        db.refresh(db_question)
    return db_question