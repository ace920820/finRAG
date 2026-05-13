from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

BASE_DIR = BACKEND_DIR / "app" / "data" / "processed"


def validate_fixtures() -> tuple[list[dict], list[dict]]:
    documents = json.loads((BASE_DIR / "documents.json").read_text(encoding="utf-8"))
    chunks = json.loads((BASE_DIR / "chunks.json").read_text(encoding="utf-8"))
    if len(documents) < 4:
        raise SystemExit("expected at least 4 documents")
    if len(chunks) < len(documents):
        raise SystemExit("expected at least one chunk per document")
    return documents, chunks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-only", action="store_true", help="validate fixtures without building retrieval indexes")
    args = parser.parse_args()

    validate_fixtures()
    if args.fixture_only:
        print("Fixture-only validation passed")
        return 0

    from app.core.retrieval.index_store import RetrievalIndexStore

    index_store = RetrievalIndexStore.load_or_build()
    index_store.save()
    print("Retrieval index build passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
