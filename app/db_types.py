from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import JSONB as JSONB_PG

class JSONB_FALLBACK(TypeDecorator):
    """
    Tipo JSONB para PostgreSQL com fallback para JSON genérico em outros dialetos.
    
    Isso permite usar JSONB em produção com PostgreSQL e ainda rodar testes
    com um banco de dados em memória como o SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Usa o tipo JSONB nativo se o banco for PostgreSQL
            return dialect.type_descriptor(JSONB_PG())
        else:
            # Usa o tipo JSON genérico (que o SQLAlchemy emula como TEXT)
            # para outros bancos de dados como o SQLite.
            return dialect.type_descriptor(self.impl)
