import json
import os
from pathlib import Path


def test_reproducibility_json_matches_expected():
    """The Java CLI must emit the accepted benchmark reproducibility summary."""
    app_root = Path(os.environ.get('APP_ROOT', '/app'))
    result_path = app_root / 'out' / 'reproducibility.json'
    assert result_path.exists(), f'Expected {result_path}'
    with result_path.open() as handle:
        payload = json.load(handle)
    assert payload == {
        'model_variant': 'vit-b-16',
        'threshold': 0.61,
        'warmup_policy': 'none',
        'analysis_profile': 'triage',
        'f1': 0.8214,
        'latency_ms': 184.0,
        'source': 'archived-predictions',
    }

