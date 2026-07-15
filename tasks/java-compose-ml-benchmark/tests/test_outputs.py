import json
import os
import random
import shutil
import subprocess
import tempfile
import zipfile
import math
from pathlib import Path
import pytest


def get_result_path():
    # Use workspace root as default if APP_ROOT not set, ensuring a writable location
    default_root = Path(__file__).resolve().parents[1]
    app_root = Path(os.environ.get('APP_ROOT', str(default_root)))
    return app_root / 'out' / 'reproducibility.json'


expected_model_variant = 'vit-b-16'
expected_warmup_policy = 'discard-15'
expected_analysis_profile = 'triage'
expected_threshold = 0.55
expected_f1 = 1.0
expected_latency = 181.6


def extract_csv_observation(line, delimiter=','):
    parts = line.strip().split(delimiter)
    if len(parts) >= 4:
        try:
            sample_id = parts[0].strip()
            score = float(parts[1].strip())
            label = int(parts[2].strip())
            latency = float(parts[3].strip())
            if label in (0, 1):
                return sample_id, score, label, latency
        except ValueError:
            pass
    return None


def extract_json_observation(line):
    try:
        data = json.loads(line.strip())
        if all(k in data for k in ('sample_id', 'score', 'label', 'latency_ms')):
            sample_id = str(data['sample_id']).strip()
            score = float(data['score'])
            label = int(data['label'])
            latency = float(data['latency_ms'])
            if label in (0, 1):
                return sample_id, score, label, latency
    except Exception:
        pass
    return None


def load_telemetry_observations(zip_path):
    entry_contents = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.endswith('/') and (name.endswith('.jsonl') or name.endswith('.csv') or name.endswith('.tsv')) and not name.startswith('__MACOSX'):
                entry_contents[name] = zf.read(name).decode('utf-8')
                
    sorted_names = sorted(entry_contents.keys())
    unique_samples = {}
    
    for name in sorted_names:
        content = entry_contents[name]
        is_tsv = name.endswith('.tsv')
        is_jsonl = name.endswith('.jsonl')
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('sample_id') or line.startswith('#'):
                continue
            
            parsed = None
            if is_jsonl:
                parsed = extract_json_observation(line)
            else:
                parsed = extract_csv_observation(line, delimiter='\t' if is_tsv else ',')
                
            if parsed is not None:
                sample_id, score, label, latency = parsed
                if sample_id not in unique_samples:
                    unique_samples[sample_id] = {
                        'sample_id': sample_id,
                        'score': score,
                        'label': label,
                        'latency_ms': latency
                    }
                    
    sorted_ids = sorted(unique_samples.keys())
    return [unique_samples[sid] for sid in sorted_ids]


def export_mutated_observations(zip_path, mutated_dict):
    entry_contents = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.endswith('/') and (name.endswith('.jsonl') or name.endswith('.csv') or name.endswith('.tsv')) and not name.startswith('__MACOSX'):
                entry_contents[name] = zf.read(name).decode('utf-8')
                
    rebuilt_entries = {}
    for name, content in entry_contents.items():
        is_tsv = name.endswith('.tsv')
        is_jsonl = name.endswith('.jsonl')
        new_lines = []
        
        for line_raw in content.splitlines():
            line = line_raw.strip()
            if not line or line.startswith('sample_id') or line.startswith('#'):
                new_lines.append(line_raw)
                continue
            
            parsed = None
            if is_jsonl:
                parsed = extract_json_observation(line)
            else:
                parsed = extract_csv_observation(line, delimiter='\t' if is_tsv else ',')
                
            if parsed is not None:
                sample_id, score, label, latency = parsed
                if sample_id in mutated_dict:
                    new_score, new_label, new_latency = mutated_dict[sample_id]
                    if is_jsonl:
                        new_lines.append(json.dumps({
                            'sample_id': sample_id,
                            'score': new_score,
                            'label': new_label,
                            'latency_ms': new_latency
                        }))
                    else:
                        delimiter = '\t' if is_tsv else ','
                        new_lines.append(f"{sample_id}{delimiter}{new_score:.6f}{delimiter}{new_label}{delimiter}{new_latency:.1f}")
                else:
                    new_lines.append(line_raw)
            else:
                new_lines.append(line_raw)
                
        rebuilt_entries[name] = "\n".join(new_lines) + "\n"
        
    temp_dir = Path(tempfile.gettempdir())
    temp_zip = temp_dir / "temp_mutated_archive.zip"
    
    with zipfile.ZipFile(temp_zip, 'w') as zf:
        for name, data in rebuilt_entries.items():
            zf.writestr(name, data)
            
    shutil.move(str(temp_zip), str(zip_path))


def calculate_expected_metrics(samples, candidates=None, recall_target=0.68, warmup_policy="discard-15"):
    if candidates is None:
        candidates = [0.55, 0.61, 0.65, 0.70]
        
    active_samples = list(samples)
    if warmup_policy.startswith("discard-"):
        try:
            percentage = int(warmup_policy.replace("discard-", ""))
            discard_count = int(math.floor((percentage / 100.0) * len(samples)))
            if 0 < discard_count < len(samples):
                active_samples = samples[discard_count:]
        except ValueError:
            pass
            
    total_positives = sum(1 for p in active_samples if p['label'] == 1)
    if total_positives == 0:
        raise ValueError("No positive labels in active samples")
        
    valid_thresholds = []
    for th in sorted(candidates):
        tp = sum(1 for p in active_samples if p['score'] >= th and p['label'] == 1)
        recall = tp / total_positives
        if recall >= recall_target:
            valid_thresholds.append(th)
            
    if not valid_thresholds:
        accepted_threshold = min(candidates)
    else:
        accepted_threshold = max(valid_thresholds)
        
    tp = sum(1 for p in active_samples if p['score'] >= accepted_threshold and p['label'] == 1)
    fp = sum(1 for p in active_samples if p['score'] >= accepted_threshold and p['label'] == 0)
    fn = sum(1 for p in active_samples if p['score'] < accepted_threshold and p['label'] == 1)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    mean_latency = sum(p['latency_ms'] for p in active_samples) / len(active_samples)
    
    return accepted_threshold, round(f1, 4), round(mean_latency, 1)


def read_warmup_policy_from_report(app_root):
    data_dir = app_root / 'data'
    try:
        report_file = next(data_dir.glob('*.md'))
        content = report_file.read_text(encoding='utf-8').lower()
        content = content.replace('`', '').replace('*', '').replace('"', '').replace("'", "")
        
        import re
        match = re.search(r'warmup(?:\s+policy)?(?:\s+is|\s+of|\s+set\s+to|\s*:\s*|\s*=\s*)\s*([a-z0-9_-]+)', content)
        if match:
            candidate = match.group(1)
            if candidate.startswith("discard-") or candidate in ("none", "linear", "cosine"):
                return candidate
    except Exception:
        pass
    return "discard-15"


def read_model_variant_from_report(app_root):
    data_dir = app_root / 'data'
    try:
        report_file = next(data_dir.glob('*.md'))
        content = report_file.read_text(encoding='utf-8').lower()
        content = content.replace('`', '').replace('*', '').replace('"', '').replace("'", "")
        
        import re
        match = re.search(r'(?:accepted|set to|final|requires|variant)\s+(?:[a-z0-9_-]+\s+){0,10}(vit-b-16|vit-b-32|resnet50|efficientnet-b0)', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "vit-b-16"


def read_analysis_profile_from_report(app_root):
    return "triage"


def read_recall_target_from_report(app_root):
    data_dir = app_root / 'data'
    try:
        report_file = next(data_dir.glob('*.md'))
        content = report_file.read_text(encoding='utf-8').lower()
        content = content.replace('`', '').replace('*', '').replace('"', '').replace("'", "")
        
        import re
        match = re.search(r'(?:recall|sensitivity)[^0-9]{0,50}(0\.[0-9]+|[0-9]+(?:\.[0-9]+)?%)', content)
        if match:
            num_str = match.group(1)
            if num_str.endswith('%'):
                return float(num_str.replace('%', '')) / 100.0
            else:
                return float(num_str)
    except Exception:
        pass
    return 0.68


def read_candidates_from_report(app_root):
    data_dir = app_root / 'data'
    try:
        report_file = next(data_dir.glob('*.md'))
        content = report_file.read_text(encoding='utf-8').lower()
        content = content.replace('`', '').replace('*', '').replace('"', '').replace("'", "")
        
        import re
        candidates = []
        for val_str in re.findall(r'0\.[0-9]+', content):
            val = float(val_str)
            if val in (0.55, 0.61, 0.65, 0.70):
                if val not in candidates:
                    candidates.append(val)
        if candidates:
            return sorted(candidates)
    except Exception:
        pass
    return [0.55, 0.61, 0.65, 0.70]


def mutate_report_in_place(app_root, seed):
    data_dir = app_root / 'data'
    try:
        report_file = next(data_dir.glob('*.md'))
        content = report_file.read_text(encoding='utf-8')
        
        random.seed(seed)
        model_variants = ['vit-b-16', 'vit-b-32', 'resnet50', 'efficientnet-b0']
        warmup_policies = ['discard-5', 'discard-10', 'discard-15', 'discard-20']
        analysis_profiles = ['triage', 'screening', 'diagnostic', 'research']
        recall_targets = [0.60, 0.65, 0.68, 0.70, 0.75]
        
        chosen_variant = random.choice(model_variants)
        chosen_warmup = random.choice(warmup_policies)
        chosen_profile = random.choice(analysis_profiles)
        chosen_recall = random.choice(recall_targets)
        
        # Replace model variant
        content = content.replace('vit-b-16', chosen_variant)
        
        # Replace warmup policy
        content = content.replace('discard-15', chosen_warmup)
        # The text says "meaning the first 15%..."
        content = content.replace('first 15%', f"first {chosen_warmup.replace('discard-', '')}%")
        
        # Replace analysis profile
        content = content.replace('triage', chosen_profile)
        
        # Replace recall target
        content = content.replace('68.0%', f"{chosen_recall * 100:.1f}%")
        content = content.replace('0.68', f"{chosen_recall:.2f}")
        
        report_file.write_text(content, encoding='utf-8')
    except Exception:
        pass


def setup_module(module):
    global expected_threshold, expected_f1, expected_latency
    global expected_model_variant, expected_warmup_policy, expected_analysis_profile
    
    result_path = get_result_path()
    if not result_path.exists():
        return
        
    app_root = Path(os.environ.get('APP_ROOT', '/app'))
    seed_str = os.environ.get("TB_VARIANT_SEED")
    
    if seed_str is not None:
        try:
            seed = int(seed_str)
        except ValueError:
            seed = 12345
            
        mutate_report_in_place(app_root, seed)
        
        zip_path = app_root / 'data' / 'archive.zip'
        if zip_path.exists():
            preds = load_telemetry_observations(zip_path)
            
            random.seed(seed)
            mutated_dict = {}
            for p in preds:
                score = p['score']
                label = p['label']
                latency = p['latency_ms']
                new_score = max(0.0, min(1.0, score + random.uniform(-0.05, 0.05)))
                new_label = label
                if random.random() < 0.05:
                    new_label = 1 - label
                new_latency = max(10.0, latency + random.uniform(-10.0, 10.0))
                mutated_dict[p['sample_id']] = (new_score, new_label, new_latency)
                
            export_mutated_observations(zip_path, mutated_dict)
            
            solve_script = Path('/solution/solve.sh')
            if not solve_script.exists():
                solve_script = app_root / 'solution' / 'solve.sh'
            if solve_script.exists():
                subprocess.run(["bash", str(solve_script)], check=True, cwd=str(app_root))
                
    expected_model_variant = read_model_variant_from_report(app_root)
    expected_warmup_policy = read_warmup_policy_from_report(app_root)
    expected_analysis_profile = read_analysis_profile_from_report(app_root)
    recall_target = read_recall_target_from_report(app_root)
    candidates = read_candidates_from_report(app_root)
    
    zip_path = app_root / 'data' / 'archive.zip'
    if zip_path.exists():
        mutated_preds = load_telemetry_observations(zip_path)
        expected_threshold, expected_f1, expected_latency = calculate_expected_metrics(
            mutated_preds, candidates=candidates, recall_target=recall_target, warmup_policy=expected_warmup_policy
        )


def test_output_file_exists():
    """Verify experimental verification summary was generated."""
    assert get_result_path().exists()


@pytest.fixture(scope="module")
def payload():
    path = get_result_path()
    with path.open() as handle:
        return json.load(handle)


def test_model_variant(payload):
    """Verify model variant parameter."""
    assert payload.get('model_variant') == expected_model_variant


def test_threshold(payload):
    """Verify classification threshold parameter matches expected dynamic threshold."""
    assert payload.get('threshold') == expected_threshold


def test_warmup_policy(payload):
    """Verify warmup policy parameter."""
    assert payload.get('warmup_policy') == expected_warmup_policy


def test_analysis_profile(payload):
    """Verify analysis profile settings."""
    assert payload.get('analysis_profile') == expected_analysis_profile


def test_f1_formatting():
    """Verify that f1 appears with 4 decimal places in raw JSON."""
    raw = get_result_path().read_text()
    # Check that f1 appears with 4 decimal places in raw JSON
    import re
    match = re.search(r'"f1"\s*:\s*([0-9.]+)', raw)
    assert match and len(match.group(1).split('.')[1]) == 4


def test_latency_ms(payload):
    """Verify calculated latency metric from experiment samples."""
    assert payload.get('latency_ms') == expected_latency


def test_source(payload):
    """Verify source metadata matches expected experiment source."""
    assert payload.get('source') == 'archived-samples'
