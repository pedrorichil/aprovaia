
# se precisar criar do zero a estrutura de pastas 
chmod +x create_project.sh
./create_project.sh


# ambiente virtual usando uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt


# Banco de dados
---
## Instalar postgres
sudo apt update
sudo apt install postgresql postgresql-contrib

### Acessar
sudo -i -u postgres
psql

### Criar banco

CREATE DATABASE nomedobanco;
CREATE USER meuusuario WITH PASSWORD 'minhasenha';
GRANT ALL PRIVILEGES ON DATABASE nomedobanco TO meuusuario;
\q  -- para sair

# importar banco de dados 
psql -U zekry -d aprovaiadb -h localhost -f script.sql



# Teste unitarios 
pip install -r requirements.txt
pip install pytest httpx pytest-mock

PYTHONPATH=. pytest -v
pytest -v