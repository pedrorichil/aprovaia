#!/bin/bash

# Nome do diretório raiz do projeto
PROJECT_DIR="."

# Criação de arquivos na raiz
touch $PROJECT_DIR/main.py
touch $PROJECT_DIR/requirements.txt

# Diretório app e seus arquivos
mkdir -p $PROJECT_DIR/app/routers

touch $PROJECT_DIR/app/__init__.py
touch $PROJECT_DIR/app/crud.py
touch $PROJECT_DIR/app/database.py
touch $PROJECT_DIR/app/models.py
touch $PROJECT_DIR/app/schemas.py
touch $PROJECT_DIR/app/security.py
touch $PROJECT_DIR/app/config.py
touch $PROJECT_DIR/app/ai_services.py

# Diretório routers e seus arquivos
touch $PROJECT_DIR/app/routers/__init__.py
touch $PROJECT_DIR/app/routers/auth.py
touch $PROJECT_DIR/app/routers/student.py
touch $PROJECT_DIR/app/routers/teacher.py
touch $PROJECT_DIR/app/routers/content.py

echo "Estrutura de projeto criada com sucesso!"
