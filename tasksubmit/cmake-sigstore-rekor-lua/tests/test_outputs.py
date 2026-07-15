import os
import subprocess
import sys
from pathlib import Path

import pytest

TEST_DIR = Path(os.environ.get("TEST_DIR", "/tests"))
APP_ROOT = Path(os.environ.get("APP_ROOT", "/app"))
BUILD_DIR = APP_ROOT / "build"
ARTIFACT_PATH = APP_ROOT / "artifacts" / "release-bundle.tar.gz"
ARTIFACT_HASH = "656bde7e1569713382a6d1c57cd88e059e30bac5b2d8ab31f6ea1d0702ae0691"

sys.path.insert(0, str(TEST_DIR / "verifier-tools"))
from rekor_mock_server import start_server  # noqa: E402


@pytest.fixture(scope="module")
def rekor_mock():
    os.environ.pop("REKOR_MOCK_WRONG_HASH", None)
    os.environ["REKOR_MOCK_ARTIFACT_HASH"] = ARTIFACT_HASH
    server = start_server()
    yield server
    server.shutdown()


def run_static_analysis() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(APP_ROOT / "tools" / "static_analysis_check.py")],
        capture_output=True,
        text=True,
        check=False,
    )


def configure_and_verify() -> subprocess.CompletedProcess[str]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["APP_ROOT"] = str(APP_ROOT)
    env["LUA_PATH"] = f"{APP_ROOT / 'lua'}/?.lua;;"
    subprocess.run(
        ["cmake", "-S", str(APP_ROOT), "-B", str(BUILD_DIR)],
        check=True,
        env=env,
    )
    return subprocess.run(
        ["cmake", "--build", str(BUILD_DIR), "--target", "verify-release"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_static_analysis_clean(rekor_mock):
    result = run_static_analysis()
    assert result.returncode == 0, result.stderr or result.stdout


def test_verify_release_passes(rekor_mock):
    """Verify that cmake --build --target verify-release succeeds when
    the artifact digest matches the Rekor log entry and all policy
    checks pass."""
    result = configure_and_verify()
    assert result.returncode == 0, result.stderr or result.stdout
    assert "verify-release: ok" in result.stdout


def test_rejects_tampered_artifact(rekor_mock):
    backup = ARTIFACT_PATH.read_bytes()
    try:
        with ARTIFACT_PATH.open("r+b") as handle:
            handle.seek(0)
            handle.write(b"X")
        result = configure_and_verify()
        assert result.returncode != 0
    finally:
        ARTIFACT_PATH.write_bytes(backup)


def test_rejects_wrong_rekor_hash(rekor_mock):
    os.environ["REKOR_MOCK_WRONG_HASH"] = "1"
    try:
        result = configure_and_verify()
        assert result.returncode != 0
        assert "digest mismatch" in (result.stderr or result.stdout)
    finally:
        os.environ.pop("REKOR_MOCK_WRONG_HASH", None)


def test_respects_preset_identity_policy(rekor_mock):
    attest_path = APP_ROOT / "release-attestations.toml"
    original = attest_path.read_text(encoding="utf-8")
    mutated = original.replace(
        'identity = "sigstore-community@rekor.dev"',
        'identity = "untrusted-signer@example.com"',
    )
    try:
        attest_path.write_text(mutated, encoding="utf-8")
        result = configure_and_verify()
        assert result.returncode != 0
        assert "identity not allowed" in (result.stderr or result.stdout)
    finally:
        attest_path.write_text(original, encoding="utf-8")


