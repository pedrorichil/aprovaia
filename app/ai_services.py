import google.generativeai as genai
from .config import settings
from . import schemas
import json

# Configura a API do Gemini com a chave das configurações
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    # A aplicação pode continuar, mas as funcionalidades de IA falharão.

def generate_embedding(text: str) -> list[float] | None:
    """
    Gera o embedding (vetor) para um dado texto usando os modelos do Gemini.
    """
    try:
        # Utiliza o modelo de embedding recomendado
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="RETRIEVAL_DOCUMENT" # Otimizado para busca de documentos
        )
        return result['embedding']
    except Exception as e:
        print(f"Erro ao gerar embedding com Gemini: {e}")
        return None

def analyze_student_error(question: schemas.Question, student_answer: str) -> dict | None:
    """
    Utiliza um modelo generativo do Gemini para analisar o erro de um aluno.
    """
    try:
        # Seleciona o modelo generativo (Flash é rápido e eficiente)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Constrói o prompt detalhado para a IA
        prompt = f"""
        Você é um tutor especialista em concursos e vestibulares. Sua tarefa é analisar o erro de um aluno.

        **Contexto da Questão:**
        - **Matéria:** {question.subject}
        - **Tópico:** {question.topic}
        - **Enunciado:** {question.content}
        - **Opções:** {json.dumps(question.options, indent=2, ensure_ascii=False)}
        - **Alternativa Correta:** {question.correct_option}

        **Resposta do Aluno:**
        O aluno marcou a alternativa: **{student_answer}**

        **Sua Análise:**
        Analise o erro mais provável do aluno. Foque em identificar a natureza do erro.
        Responda em formato JSON, com as seguintes chaves:
        - "error_type": Uma categoria para o erro. Escolha uma das seguintes: ["conceptual_confusion", "misinterpretation", "calculation_error", "inattention", "unknown"].
        - "brief_explanation": Uma explicação curta e direta (máximo 2 frases) sobre o erro, como se você estivesse falando com o aluno.
        - "detailed_feedback": Um feedback mais completo, explicando o conceito correto e por que a alternativa do aluno está errada.

        **Exemplo de Resposta JSON:**
        {{
          "error_type": "conceptual_confusion",
          "brief_explanation": "Você parece ter confundido os conceitos de 'soberania' e 'autonomia'. A soberania é um atributo do Estado Federal, enquanto a autonomia é dos estados-membros.",
          "detailed_feedback": "A questão aborda a organização do Estado brasileiro. A alternativa correta aponta para a soberania da República Federativa do Brasil. A alternativa que você marcou fala em soberania dos estados, mas na verdade, os estados (como São Paulo ou Bahia) possuem autonomia política e administrativa, mas não soberania, que é a característica do país como um todo no cenário internacional."
        }}

        **Sua resposta JSON:**
        """

        response = model.generate_content(prompt)
        
        # Limpa e parseia a resposta para garantir que é um JSON válido
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)

    except Exception as e:
        print(f"Erro ao analisar erro com Gemini: {e}")
        return {
            "error_type": "analysis_failed",
            "brief_explanation": "Não foi possível realizar a análise da sua resposta no momento.",
            "detailed_feedback": "Ocorreu um erro ao tentar se comunicar com o serviço de IA. Tente novamente mais tarde."
        }

def grade_essay_with_gemini(essay_text: str, theme: str) -> dict | None:
    """
    Utiliza o Gemini para corrigir uma redação com base nos critérios do ENEM,
    forçando uma resposta em JSON estruturado.
    """
    try:
        # Define o schema JSON que a API do Gemini deve retornar.
        # Isto corresponde ao schema Pydantic EssayGradeResponse.
        json_schema = {
            "type": "OBJECT",
            "properties": {
                "feedback_geral": {"type": "STRING"},
                "nota_total": {"type": "NUMBER"},
                "criterios": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "nome": {"type": "STRING"},
                            "nota": {"type": "NUMBER"},
                            "feedback": {"type": "STRING"}
                        },
                        "required": ["nome", "nota", "feedback"]
                    }
                }
            },
            "required": ["feedback_geral", "nota_total", "criterios"]
        }

        # Configura o modelo para usar o modo de geração JSON
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json", "response_schema": json_schema}
        )
        
        # Constrói o prompt
        prompt = f"""
        Aja como um corretor de redações do ENEM. Avalie a seguinte redação com o tema "{theme}".
        Forneça um feedback detalhado para cada um dos 5 critérios do ENEM (Competência 1: Domínio da norma culta; Competência 2: Compreensão do tema e estrutura; Competência 3: Argumentação; Competência 4: Conhecimento dos mecanismos linguísticos; Competência 5: Proposta de intervenção).
        Dê uma nota de 0 a 200 para cada critério. A nota total deve ser a soma das notas dos critérios.
        Retorne a resposta estritamente no formato JSON solicitado.

        Texto da redação:
        \"\"\"
        {essay_text}
        \"\"\"
        """

        response = model.generate_content(prompt)
        return json.loads(response.text)

    except Exception as e:
        print(f"Erro em grade_essay_with_gemini: {e}")
        return None

def ask_tutor_with_gemini(question: str, context: str | None) -> str | None:
    """Usa o Gemini para responder a uma dúvida de um aluno."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Você é um tutor amigável e experiente. Um aluno tem a seguinte dúvida: "{question}".
        Se houver um contexto de estudo, use-o para basear a sua resposta.
        Contexto: \"\"\"{context or 'Nenhum'}\"\"\".
        Explique o conceito de forma clara e simples, como se estivesse a dar uma aula particular.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro em askTutor:", e)
        return None

def summarize_content_with_gemini(text_to_summarize: str) -> str | None:
    """Usa o Gemini para resumir um texto."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Resuma o seguinte texto em 3 a 5 pontos principais (bullet points), focando nas ideias mais importantes para quem está a estudar para uma prova.
        Texto: \"\"\"{text_to_summarize}\"\"\"
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro em summarizeContent:", e)
        return None


def structure_exam_from_text(text: str) -> dict | None:
    """
    Usa o Gemini para ler o texto de uma prova e estruturá-lo em JSON.
    """
    try:
        json_schema = {
            "type": "OBJECT",
            "properties": {
                "questions": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "subject": {"type": "STRING"},
                            "topic": {"type": "STRING"},
                            "content": {"type": "STRING"},
                            "options": {
                                "type": "OBJECT",
                                "properties": {
                                    "A": {"type": "STRING"}, "B": {"type": "STRING"},
                                    "C": {"type": "STRING"}, "D": {"type": "STRING"},
                                    "E": {"type": "STRING"}
                                },
                                "required": ["A", "B", "C", "D", "E"]
                            }
                        },
                        "required": ["subject", "topic", "content", "options"]
                    }
                }
            },
            "required": ["questions"]
        }
        
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json", "response_schema": json_schema}
        )
        
        prompt = f"""
        Você é um assistente especialista em processar documentos de provas de concurso.
        Analise o texto a seguir, que foi extraído de um PDF de uma prova.
        Identifique cada questão individualmente. Para cada questão, extraia a matéria (subject), um tópico específico (topic), o enunciado completo (content) e as 5 alternativas (options) de A a E.
        Ignore cabeçalhos, rodapés, números de página e textos institucionais. Foque apenas no conteúdo das questões.
        Retorne um objeto JSON contendo uma única chave "questions", que é uma lista de objetos, cada um representando uma questão.

        Texto da prova:
        \"\"\"
        {text}
        \"\"\"
        """
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro ao estruturar prova com Gemini: {e}")
        return None
