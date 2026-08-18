from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "index.sqlite3"
CONFIG_PATH = ROOT / "config" / "standards.json"


def load_registry() -> list[dict]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["standards"]


def identify_standard(path: Path) -> tuple[str, str]:
    name = path.stem.lower()
    registry = load_registry()
    for item in registry:
        aliases = [item["code"], *item.get("aliases", [])]
        if any(alias.lower().replace("/", " ") in name.replace("-", " ") for alias in aliases):
            return item["code"], item["edition"]
    return "Unknown", "Unknown"


def normalize(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_chunks(document_id: str, page_number: int, text: str, max_chars: int = 3500) -> list[tuple]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[tuple] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 1 > max_chars:
            chunks.append((current, None))
            current = ""
        current = f"{current} {paragraph}".strip()
    if current:
        chunks.append((current, None))

    result = []
    for i, (chunk_text, section) in enumerate(chunks):
        chunk_id = hashlib.sha1(f"{document_id}:{page_number}:{i}:{chunk_text}".encode()).hexdigest()
        result.append((chunk_id, document_id, page_number, section, None, chunk_text))
    return result


def initialize_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            code TEXT NOT NULL,
            edition TEXT NOT NULL,
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            page INTEGER NOT NULL,
            section TEXT,
            heading TEXT,
            text TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(document_id)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            chunk_id UNINDEXED,
            document_id UNINDEXED,
            text,
            content='chunks',
            content_rowid='rowid'
        );
        """
    )


def ingest_file(conn: sqlite3.Connection, path: Path) -> int:
    code, edition = identify_standard(path)
    document_id = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:16]
    title = path.stem

    conn.execute(
        "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?)",
        (document_id, str(path), code, edition, title),
    )
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    conn.execute("DELETE FROM chunks_fts WHERE document_id = ?", (document_id,))

    count = 0
    with fitz.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            if not text.strip():
                continue
            for chunk in make_chunks(document_id, page_number, normalize(text)):
                conn.execute("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)", chunk)
                conn.execute("INSERT INTO chunks_fts(chunk_id, document_id, text) VALUES (?, ?, ?)", (chunk[0], chunk[1], chunk[5]))
                count += 1

    return count


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    initialize_db(conn)

    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs found in {RAW_DIR}")

    for path in pdfs:
        try:
            count = ingest_file(conn, path)
            conn.commit()
            code, edition = identify_standard(path)
            print(f"INGESTED  {path.name}  | {code} {edition} | {count} chunks")
        except Exception as exc:
            conn.rollback()
            print(f"ERROR     {path.name}  | {exc}")

    conn.close()


if __name__ == "__main__":
    main()
