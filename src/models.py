from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    document_id: str
    path: Path
    code: str
    edition: str
    title: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    page: int
    section: str | None
    heading: str | None
    text: str

    @property
    def citation(self) -> str:
        section = f" §{self.section}" if self.section else ""
        return f"{self.document_id}{section}, p. {self.page}"
