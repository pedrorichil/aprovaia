import chromadb
from app.config import settings

# Inicializa o cliente ChromaDB com armazenamento persistente
client = chromadb.PersistentClient(path=settings.CHROMA_PATH)

# Cria ou obtém a coleção (semelhante a uma tabela)
question_collection = client.get_or_create_collection(name="questions")

def upsert_question(question_id: str, embedding: list[float], metadata: dict):
    """
    Insere ou atualiza um vetor de questão no ChromaDB.
    """
    try:
        question_collection.upsert(
            ids=[question_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        print(f"Vetor para a questão {question_id} inserido com sucesso no ChromaDB.")
    except Exception as e:
        print(f"Erro ao inserir vetor no ChromaDB: {e}")

def search_similar_questions(embedding: list[float], n_results: int = 5, subject: str = None):
    """
    Busca por questões vetorialmente similares.
    """
    where_filter = {}
    if subject:
        where_filter["subject"] = subject

    results = question_collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where_filter if where_filter else None
    )
    return results

