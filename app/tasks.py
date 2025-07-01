from celery_worker import celery_app
from app.database import SessionLocal
from app import crud, ai_services, schemas, vector_db
import fitz
import uuid
import os


@celery_app.task
def analyze_student_answer(answer_id: str):
    """
    Tarefa Celery para analisar a resposta de um aluno.
    Busca a resposta no DB, chama a IA (se errada) e atualiza a proficiência.
    """
    db = SessionLocal()
    try:
        answer = db.query(crud.models.StudentAnswer).filter_by(id=uuid.UUID(answer_id)).first()
        if answer:
            crud.run_ai_analysis_and_update_proficiency(db, answer)
    finally:
        db.close()

@celery_app.task
def process_exam_pdf(file_path: str, contest: str, year: int):
    """
    Tarefa Celery para processar um PDF de prova com lógica real.
    """
    db = SessionLocal()
    try:
        full_text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                full_text += page.get_text()
        
        if not full_text: return

        structured_questions = ai_services.structure_exam_from_text(full_text)
        if not structured_questions or "questions" not in structured_questions: return

        for q_data in structured_questions["questions"]:
            q_data['source'] = f"{contest} {year}"
            question_schema = schemas.QuestionCreate(**q_data)
            
            # 1. Guarda no PostgreSQL primeiro para obter um ID estável
            db_question = crud.create_question(db, question=question_schema)
            if not db_question: continue
            
            question_id_str = str(db_question.id)

            # 2. Gera o embedding
            embedding = ai_services.generate_embedding(text=question_schema.content)
            if not embedding: continue

            # 3. Insere no ChromaDB usando o ID do PostgreSQL
            metadata = {"subject": db_question.subject, "topic": db_question.topic, "source": db_question.source}
            vector_db.upsert_question(question_id=question_id_str, embedding=embedding, metadata=metadata)
            
            # 4. Atualiza a questão no PostgreSQL com o seu próprio ID como vector_id
            crud.update_question_vector_id(db, question_id=db_question.id, vector_id=question_id_str)
            print(f"Questão '{q_data['content'][:30]}...' processada e vetorizada.")

    finally:
        if os.path.exists(file_path): os.remove(file_path)
        db.close()
