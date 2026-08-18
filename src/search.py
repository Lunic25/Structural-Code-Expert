from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "index.sqlite3"


def search(query: str, limit: int = 8) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT c.chunk_id, c.document_id, c.page, c.section, c.heading, c.text,
               d.code, d.edition, d.title
        FROM chunks_fts f
        JOIN chunks c ON c.chunk_id = f.chunk_id
        JOIN documents d ON d.document_id = c.document_id
        WHERE chunks_fts MATCH ?
        ORDER BY bm25(chunks_fts)
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit("Index not found. Run: python -m src.ingest")
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        raise SystemExit("Usage: python -m src.search \"wind pressure\"")

    for i, result in enumerate(search(query), start=1):
        print(f"\n[{i}] {result['code']} {result['edition']} | {result['title']} | p. {result['page']}")
        print(result['text'])


if __name__ == "__main__":
    main()
