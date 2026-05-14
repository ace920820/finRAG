from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

BASE_DIR = BACKEND_DIR / "app" / "data" / "processed"
INDEX_DIR = BACKEND_DIR / "app" / "data" / "index"


def validate_fixtures(processed_dir: Path = BASE_DIR) -> tuple[list[dict], list[dict]]:
    documents = json.loads((processed_dir / "documents.json").read_text(encoding="utf-8"))
    chunks = json.loads((processed_dir / "chunks.json").read_text(encoding="utf-8"))
    if not documents:
        raise SystemExit("expected at least one document")
    if len(chunks) < len(documents):
        raise SystemExit("expected at least one chunk per document")
    return documents, chunks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-only", action="store_true", help="validate fixtures without building retrieval indexes")
    parser.add_argument("--processed-dir", type=Path, default=Path(os.environ.get("FINRAG_PROCESSED_DATA_DIR", BASE_DIR)))
    parser.add_argument("--index-dir", type=Path, default=Path(os.environ.get("FINRAG_INDEX_DIR", INDEX_DIR)))
    args = parser.parse_args()

    validate_fixtures(args.processed_dir)
    if args.fixture_only:
        print("Fixture-only validation passed")
        return 0

    os.environ["FINRAG_PROCESSED_DATA_DIR"] = str(args.processed_dir.resolve())
    os.environ["FINRAG_INDEX_DIR"] = str(args.index_dir.resolve())

    from app.core.config import get_settings
    from app.core.ingestion.fixture_loader import _processed_dir
    from app.core.retrieval.index_store import RetrievalIndexStore

    get_settings.cache_clear()
    _processed_dir.cache_clear()

    index_store = RetrievalIndexStore.load_or_build(force_rebuild=True)
    index_store.save()
    print("Retrieval index build passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
