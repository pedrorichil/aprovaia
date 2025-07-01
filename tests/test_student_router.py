from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Question, StudentAnswer, User
from uuid import uuid4

def test_submit_answer_success(test_client: TestClient, db_session: Session, student_auth_token: str, mocker):
    mock_task = mocker.patch("app.tasks.analyze_student_answer.delay")
    question = Question(id=uuid4(), content="Teste?", options={"A": "1", "B": "2"}, correct_option="A", subject="Teste", topic="Teste")
    db_session.add(question)
    db_session.commit()
    response = test_client.post(
        "/student/assessment/answer",
        headers={"Authorization": f"Bearer {student_auth_token}"},
        json={"question_id": str(question.id), "selected_option": "A"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["correct_option"] == "A"
    assert "answer_id" in data
    mock_task.assert_called_once_with(data["answer_id"])


def test_get_answer_analysis_success(test_client: TestClient, db_session: Session, student_user: User, student_auth_token: str):
    analysis_data = {"error_type": "conceptual_confusion", "explanation": "Teste"}
    answer = StudentAnswer(
        id=uuid4(), 
        profile_id=student_user.profile.id,
        question_id=uuid4(), 
        selected_option="B", 
        is_correct=False, 
        ai_analysis=analysis_data
    )
    db_session.add(answer)
    db_session.commit()
    response = test_client.get(
        f"/student/answers/{answer.id}/analysis",
        headers={"Authorization": f"Bearer {student_auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ai_analysis"]["explanation"] == "Teste"


# CORREÇÃO: Adicionado `mocker` como argumento da função de teste.
def test_get_answer_analysis_unauthorized(test_client: TestClient, db_session: Session, student_user: User, admin_user: User, admin_auth_token: str, mocker):
    answer = StudentAnswer(id=uuid4(), profile_id=student_user.profile.id, question_id=uuid4(), selected_option="B", is_correct=False)
    db_session.add(answer)
    db_session.commit()
    
    mocker.patch("app.security.get_current_active_user_with_role", return_value=admin_user)

    response = test_client.get(
        f"/student/answers/{answer.id}/analysis",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    assert response.status_code == 403
