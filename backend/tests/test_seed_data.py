import os
from pathlib import Path
import json
import subprocess


def test_seed_and_fixture_only_build(tmp_path):
    backend_dir = Path(__file__).resolve().parents[1]
    sandbox = tmp_path / 'processed'
    env = {**os.environ, 'FINRAG_PROCESSED_DATA_DIR': str(sandbox)}
    subprocess.run(['python3', 'scripts/seed_data.py'], cwd=backend_dir, check=True, env=env)
    subprocess.run(
        ['python3', 'scripts/build_index.py', '--fixture-only', '--processed-dir', str(sandbox)],
        cwd=backend_dir,
        check=True,
        env=env,
    )

    documents = json.loads((sandbox / 'documents.json').read_text(encoding='utf-8'))
    chunks = json.loads((sandbox / 'chunks.json').read_text(encoding='utf-8'))
    demo_cases = json.loads((sandbox / 'demo_cases.json').read_text(encoding='utf-8'))

    assert len(documents) >= 4
    assert len(chunks) >= len(documents)
    assert len(demo_cases) >= 3
