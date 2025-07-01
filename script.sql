-- Habilita a extensão pgcrypto para gerar UUIDs, caso ainda não esteja habilitada.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Cria um tipo ENUM para garantir a integridade dos papéis de usuário.
CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin');

-- Tabela para Organizações/Clientes (Tenants)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela para Usuários do Sistema
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_tenant
        FOREIGN KEY(tenant_id)
        REFERENCES tenants(id)
        ON DELETE CASCADE
);

-- Tabela para Perfis de Alunos e Professores
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    current_goal VARCHAR(255), -- Ex: 'ENEM', 'OAB', 'PRF'
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Tabela para Matrículas (ligação entre Professor e Aluno)
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL,
    student_id UUID NOT NULL,
    CONSTRAINT fk_teacher_profile
        FOREIGN KEY(teacher_id)
        REFERENCES profiles(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_student_profile
        FOREIGN KEY(student_id)
        REFERENCES profiles(id)
        ON DELETE CASCADE,
    UNIQUE (teacher_id, student_id) -- Garante que um aluno não pode ser matriculado duas vezes pelo mesmo professor
);

-- Tabela para o Banco de Questões
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    options JSONB NOT NULL, -- Ex: { "A": "Texto A", "B": "Texto B", ... }
    correct_option VARCHAR(10) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    source VARCHAR(255), -- Ex: 'ENEM 2023', 'PRF 2021'
    vector_id VARCHAR(255) UNIQUE -- ID correspondente no banco vetorial
);

-- Tabela para as Respostas dos Alunos
CREATE TABLE student_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL,
    question_id UUID NOT NULL,
    selected_option VARCHAR(10) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    time_taken_ms INTEGER, -- Tempo em milissegundos
    ai_analysis JSONB, -- { "error_type": "...", "explanation": "..." }
    answered_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_profile
        FOREIGN KEY(profile_id)
        REFERENCES profiles(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_question
        FOREIGN KEY(question_id)
        REFERENCES questions(id)
        ON DELETE RESTRICT -- Impede que uma questão seja deletada se houver respostas associadas
);

-- Tabela para o Mapa de Competências (Proficiência) do Aluno
CREATE TABLE student_proficiency_map (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL,
    topic VARCHAR(255) NOT NULL,
    proficiency_score REAL NOT NULL CHECK (proficiency_score >= 0.0 AND proficiency_score <= 1.0),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_profile
        FOREIGN KEY(profile_id)
        REFERENCES profiles(id)
        ON DELETE CASCADE,
    UNIQUE (profile_id, topic) -- Garante que cada aluno tenha apenas um score por tópico
);


CREATE INDEX idx_users_tenant_id ON users(tenant_id);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);

CREATE INDEX idx_enrollments_teacher_id ON enrollments(teacher_id);
CREATE INDEX idx_enrollments_student_id ON enrollments(student_id);

CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_topic ON questions(topic);

CREATE INDEX idx_student_answers_profile_id ON student_answers(profile_id);
CREATE INDEX idx_student_answers_question_id ON student_answers(question_id);

CREATE INDEX idx_student_proficiency_map_profile_id ON student_proficiency_map(profile_id);
CREATE INDEX idx_student_proficiency_map_topic ON student_proficiency_map(topic);

