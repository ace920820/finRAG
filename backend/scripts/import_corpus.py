from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.ingestion.corpus_importer import ImportDefaults, import_corpus

DEFAULT_RAW_ROOT = BACKEND_DIR / "app" / "data" / "raw"
DEFAULT_PROCESSED_DIR = BACKEND_DIR / "app" / "data" / "processed"
DEFAULT_INDEX_DIR = BACKEND_DIR / "app" / "data" / "index"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import raw Markdown/text into FinRAG processed corpus files.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--source-dir", type=Path, help="Optional direct Markdown/text source directory.")
    parser.add_argument("--collection-name", default="finrag-corpus")
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    parser.add_argument("--default-company", default="未知")
    parser.add_argument("--default-doc-type", default="research_report", choices=("financial_report", "research_report", "news"))
    parser.add_argument("--default-date", default="unknown")
    parser.add_argument("--default-company-aliases", default="")
    parser.add_argument("--target-chars", type=int, default=900)
    parser.add_argument("--rebuild-index", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    aliases = tuple(item.strip() for item in args.default_company_aliases.split(",") if item.strip())
    result = import_corpus(
        raw_root=args.raw_root,
        source_dir=args.source_dir,
        collection_name=args.collection_name,
        processed_dir=args.processed_dir,
        defaults=ImportDefaults(
            company=args.default_company,
            doc_type=args.default_doc_type,
            date=args.default_date,
            company_aliases=aliases,
        ),
        target_chars=args.target_chars,
    )
    print("Corpus import finished.")
    print(f"  Documents: {len(result.documents)}")
    print(f"  Chunks: {len(result.chunks)}")
    print(f"  Documents JSON: {result.documents_path}")
    print(f"  Chunks JSON: {result.chunks_path}")
    print(f"  Table facts: {len(result.facts)}")
    print(f"  Table facts JSON: {result.facts_path}")

    if args.rebuild_index:
        env = os.environ.copy()
        env["FINRAG_PROCESSED_DATA_DIR"] = str(args.processed_dir.resolve())
        env["FINRAG_INDEX_DIR"] = str(args.index_dir.resolve())
        subprocess.run([sys.executable, str(BACKEND_DIR / "scripts" / "build_index.py")], cwd=BACKEND_DIR, check=True, env=env)
        print(f"  Index dir: {args.index_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
