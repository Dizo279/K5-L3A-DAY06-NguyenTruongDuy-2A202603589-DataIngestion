"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if not database_url:
            raise ValueError("database_url is required")
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")
        self.database_url = database_url
        self.dimensions = dimensions
        self.table_name = "day6_chunks"

    def create_schema(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, chunk_id)
                    )
                    """
                )
                cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_strategy_idx "
                    f"ON {self.table_name} (strategy)"
                )
            connection.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Replace the indexed chunks for each source document atomically.

        When re-ingesting changed source documents, remove obsolete chunks too.
        """
        if not strategy:
            raise ValueError("strategy is required")
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise ValueError("vector dimension does not match the store")
        if not chunks:
            return

        document_ids = {chunk.document_id for chunk in chunks}
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                for document_id in document_ids:
                    cursor.execute(
                        f"DELETE FROM {self.table_name} WHERE strategy = %s AND document_id = %s",
                        (strategy, document_id),
                    )
                for chunk, vector in zip(chunks, vectors):
                    cursor.execute(
                        f"""
                        INSERT INTO {self.table_name}
                            (strategy, chunk_id, document_id, source, page, text, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (strategy, chunk_id) DO UPDATE SET
                            document_id = EXCLUDED.document_id,
                            source = EXCLUDED.source,
                            page = EXCLUDED.page,
                            text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """,
                        (
                            strategy,
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.source,
                            chunk.page,
                            chunk.text,
                            Jsonb(chunk.metadata),
                            self._vector_literal(vector),
                        ),
                    )
            connection.commit()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Search by cosine similarity and apply permitted metadata filters.

        Return chunk ID, text, score and metadata. Parameterize user-supplied values.
        """
        if not strategy:
            raise ValueError("strategy is required")
        if len(query_vector) != self.dimensions:
            raise ValueError("query vector dimension does not match the store")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        allowed_filters = {
            "section", "year", "version", "category", "audience",
            "language", "effective_date", "document_type",
        }
        filters = filters or {}
        unknown = set(filters) - allowed_filters
        if unknown:
            raise ValueError(f"unsupported metadata filters: {sorted(unknown)}")

        clauses = ["strategy = %s"]
        params: list[Any] = [strategy]
        for key, value in filters.items():
            clauses.append("metadata ->> %s = %s")
            params.extend([key, str(value)])
        where = " AND ".join(clauses)
        vector_literal = self._vector_literal(query_vector)
        query_params: list[Any] = [vector_literal, *params, vector_literal, top_k]
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT chunk_id, document_id, source, page, text, metadata,
                           1 - (embedding <=> %s::vector) AS score
                    FROM {self.table_name}
                    WHERE {where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    query_params,
                )
                rows = cursor.fetchall()
        return [
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "source": row[2],
                "page": row[3],
                "text": row[4],
                "metadata": row[5],
                "score": float(row[6]),
            }
            for row in rows
        ]

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(format(float(value), ".12g") for value in vector) + "]"
