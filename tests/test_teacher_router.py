from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User
from uuid import uuid4

# CORREÇÃO: Adicionado `admin_auth_token` como argumento e usado no header.
def test_get_dashboard_success(test_client: TestClient, mocker, admin_user: User, admin_auth_token: str):
    admin_user.role = 'teacher'
    mocker.patch("app.security.get_current_active_user_with_role", return_value=admin_user)
    mock_data = {
        "class_average_score": 0.8,
        "most_difficult_topics": [{"topic": "Teste", "average": 0.5}],
        "engagement": {"active_students": 1, "total_students": 1}
    }
    mocker.patch("app.crud.get_teacher_dashboard_data", return_value=mock_data)
    
    response = test_client.get(
        "/teacher/dashboard",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["class_average_score"] == 0.8


# CORREÇÃO: Adicionado `admin_auth_token` como argumento e usado no header.
def test_get_student_details_success(test_client: TestClient, mocker, student_user: User, admin_user: User, admin_auth_token: str):
    admin_user.role = 'teacher'
    mocker.patch("app.security.get_current_active_user_with_role", return_value=admin_user)
    mock_data = {
        "profile": {"id": str(student_user.profile.id), "user_id": str(student_user.id), "full_name": student_user.profile.full_name, "current_goal": None},
        "proficiency_map": [],
        "recent_errors": []
    }
    mocker.patch("app.crud.get_student_details_for_teacher", return_value=mock_data)
    
    response = test_client.get(
        f"/teacher/students/{student_user.profile.id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["profile"]["full_name"] == "Aluno de Teste"
