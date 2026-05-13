from pathlib import Path
import json
import subprocess


def test_seed_and_fixture_only_build():
    backend_dir = Path(__file__).resolve().parents[1]
    subprocess.run(['python3', 'scripts/seed_data.py'], cwd=backend_dir, check=True)
    subprocess.run(['python3', 'scripts/build_index.py', '--fixture-only'], cwd=backend_dir, check=True)

    base = backend_dir / 'app' / 'data' / 'processed'
    documents = json.loads((base / 'documents.json').read_text(encoding='utf-8'))
    chunks = json.loads((base / 'chunks.json').read_text(encoding='utf-8'))
    demo_cases = json.loads((base / 'demo_cases.json').read_text(encoding='utf-8'))

    assert len(documents) >= 4
    assert len(chunks) >= len(documents)
    assert len(demo_cases) >= 3
