# Structural Code Expert

AI structural-engineering code expert for edition-aware retrieval, reasoning, and citations from authoritative standards.

## Current milestone: local standards search

The first working layer is deliberately simple and inspectable:

`licensed PDFs -> PyMuPDF extraction -> normalized chunks -> SQLite FTS5 -> ranked search`

Standards PDFs and extracted text stay local and are ignored by Git. Do not commit copyrighted standards.

### Initial standards registry

- ASCE 7-22
- IBC 2024 / 2021
- NDS 2024 / 2018
- SDPWS 2021
- AISC 360-22 / 360-16
- ACI 318-25 / 318-19

The registry is configuration, not proof that a document is present. The ingestion script identifies documents from filenames and reports `Unknown` when it cannot confidently identify an edition.

## Setup

From the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Put licensed PDFs in `data/raw/`.

## Ingest the standards

```powershell
python -m src.ingest
```

This creates the local ignored database at `data/index.sqlite3`.

## Search the code library

```powershell
python -m src.search "wind pressure"
python -m src.search "snow drift"
python -m src.search "load combinations"
```

## Next milestone

Add a structural-code answer layer that:

1. identifies the governing standard and edition,
2. retrieves relevant provisions,
3. preserves page/section provenance,
4. distinguishes source text from interpretation,
5. generates an answer with citations,
6. refuses to invent a requirement when evidence is insufficient.

After that we will add semantic retrieval, tables/figures, section-aware parsing, jurisdiction/adoption logic, and an evaluation suite.
