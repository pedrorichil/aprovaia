from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Question
from uuid import uuid4
import io

def test_upload_exam_success(test_client: TestClient, admin_auth_token: str, mocker):
    # CORREÇÃO: Configura o mock para que o atributo 'id' retorne uma string.
    mock_task = mocker.patch("app.tasks.process_exam_pdf.delay")
    mock_task.return_value.id = "fake-task-id-12345"
    
    fake_pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    fake_pdf = ("test.pdf", io.BytesIO(fake_pdf_content), "application/pdf")

    response = test_client.post(
        "/admin/exams/upload",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
        data={"contest": "ENEM", "year": 2025},
        files={"file": fake_pdf}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "Prova recebida e agendada para processamento."
    assert data["task_id"] == "fake-task-id-12345"
    mock_task.assert_called_once()


def test_update_answer_key_success(test_client: TestClient, db_session: Session, admin_auth_token: str):
    question = Question(id=uuid4(), content="Teste?", options={"A": "1", "B": "2"}, correct_option="A", subject="Teste", topic="Teste")
    db_session.add(question)
    db_session.commit()
    response = test_client.put(
        f"/admin/questions/{question.id}/answer-key",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
        json={"correct_option": "B"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct_option"] == "B"
    db_session.refresh(question)
    assert question.correct_option == "B"

