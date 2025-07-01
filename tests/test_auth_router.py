from fastapi.testclient import TestClient
from app.models import User

def test_login_success(test_client: TestClient, student_user: User):
    """Testa o login bem-sucedido e a nova estrutura da resposta."""
    # CORREÇÃO: Removido o prefixo /api/v1 e usando Form Data
    response = test_client.post(
        "/auth/login",
        data={"username": student_user.email, "password": "senha123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == student_user.email
    assert data["user"]["role"] == "student"

def test_login_wrong_password(test_client: TestClient, student_user: User):
    """Testa a falha de login com a senha incorreta."""
    # CORREÇÃO: Removido o prefixo /api/v1 e usando Form Data
    response = test_client.post(
        "/auth/login",
        data={"username": student_user.email, "password": "senhaErrada"}
    )
    assert response.status_code == 401
