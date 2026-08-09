"""
Regression tests for issue #20: requirements.txt and requirements-prod.txt
diverged by many major versions on critical packages, and prod carried
obsolete/unused deps (redis, google-generativeai, langchain-openai).

These tests are hermetic: pure file parsing with the standard library only.
They do NOT import the app and never touch the network. They lock in that the
two requirement files stay one coherent dependency contract, that removed
packages never return, and that env.example no longer advertises unused config.
"""
import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = REPO_ROOT / "requirements.txt"
REQUIREMENTS_PROD = REPO_ROOT / "requirements-prod.txt"
ENV_EXAMPLE = REPO_ROOT / "env.example"

# Packages that must never reappear in EITHER requirements file.
OBSOLETE_PACKAGES = ["redis", "google-generativeai", "langchain-openai"]

# Runtime deps that prod MUST ship so it does not ImportError at boot.
REQUIRED_PROD_PACKAGES = [
    "groq",
    "langchain",
    "langchain-groq",
    "langchain-core",
    "langchain-text-splitters",
    "fastapi",
    "uvicorn",
    "pydantic",
    "boto3",
    "huggingface_hub",
    "python-multipart",
    "python-dotenv",
    "requests",
    "aiohttp",
]

# The only intentional dev-only difference: test tooling prod never imports.
TEST_ONLY_PACKAGES = {"pytest", "pytest-asyncio", "httpx"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canonicalize(name: str) -> str:
    """PEP 503 canonical form: lowercase, collapse runs of -/_/. to a single -."""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _split_name_and_spec(requirement: str):
    """
    Split a requirement line into (bare_name, extras, version_spec).

    Given ``huggingface_hub[inference,cli]>=0.21.0`` returns
    ``("huggingface_hub", "[inference,cli]", ">=0.21.0")``.
    """
    # Strip inline comments and surrounding whitespace.
    line = requirement.split("#", 1)[0].strip()
    # Name is everything up to the first version operator or extras bracket.
    m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?(.*)$", line)
    assert m, f"Could not parse requirement line: {requirement!r}"
    bare_name = m.group(1)
    extras = m.group(2) or ""
    version_spec = m.group(3).strip()
    return bare_name, extras, version_spec


def _parse_requirements(path: Path):
    """
    Parse a requirements file into a dict of
    {canonical_name: full_spec_string} where full_spec_string preserves
    extras + version specifier (so an extras mismatch is caught) but the KEY
    excludes the extras bracket.
    """
    assert path.exists(), f"Missing requirements file: {path}"
    result = {}
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        bare_name, extras, version_spec = _split_name_and_spec(line)
        canonical = _canonicalize(bare_name)
        full_spec = f"{extras}{version_spec}"
        result[canonical] = full_spec
    return result


# ---------------------------------------------------------------------------
# Fixtures / module-level parses
# ---------------------------------------------------------------------------

DEV = _parse_requirements(REQUIREMENTS)
PROD = _parse_requirements(REQUIREMENTS_PROD)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("package", OBSOLETE_PACKAGES)
def test_obsolete_package_absent_from_dev(package):
    canonical = _canonicalize(package)
    assert canonical not in DEV, (
        f"Obsolete package {package!r} must not be in requirements.txt "
        f"(it is unused / was removed for issue #20)."
    )


@pytest.mark.parametrize("package", OBSOLETE_PACKAGES)
def test_obsolete_package_absent_from_prod(package):
    canonical = _canonicalize(package)
    assert canonical not in PROD, (
        f"Obsolete package {package!r} must not be in requirements-prod.txt "
        f"(it is unused / was removed for issue #20)."
    )


def test_shared_packages_have_identical_specs():
    """Core regression: any package in BOTH files must pin the same spec."""
    shared = sorted(set(DEV) & set(PROD))
    assert shared, "Expected overlapping packages between dev and prod files."
    mismatches = {
        name: (DEV[name], PROD[name])
        for name in shared
        if DEV[name] != PROD[name]
    }
    assert not mismatches, (
        "requirements.txt and requirements-prod.txt disagree on version "
        f"specifiers for shared packages: {mismatches}. They must be identical."
    )


def test_prod_is_name_subset_of_dev():
    """No prod-only package: every prod package must exist in dev."""
    prod_only = sorted(set(PROD) - set(DEV))
    assert not prod_only, (
        f"requirements-prod.txt contains packages absent from requirements.txt: "
        f"{prod_only}. Prod must be a strict subset of dev."
    )


@pytest.mark.parametrize("package", REQUIRED_PROD_PACKAGES)
def test_required_runtime_package_present_in_prod(package):
    canonical = _canonicalize(package)
    assert canonical in PROD, (
        f"Runtime dependency {package!r} is missing from requirements-prod.txt; "
        f"production would ImportError without it."
    )


def test_only_test_tooling_is_dev_only():
    """Locks the intentional difference: dev - prod == the test tools exactly."""
    dev_only = set(DEV) - set(PROD)
    expected = {_canonicalize(p) for p in TEST_ONLY_PACKAGES}
    assert dev_only == expected, (
        f"Packages present in dev but not prod must be exactly the test-only "
        f"tools {sorted(expected)}, but got {sorted(dev_only)}. A runtime dep may "
        f"have gone missing from prod (or a new test tool leaked in)."
    )


def test_env_example_has_no_openai_key():
    assert ENV_EXAMPLE.exists(), f"Missing env.example: {ENV_EXAMPLE}"
    offending = [
        line
        for line in ENV_EXAMPLE.read_text().splitlines()
        if re.match(r"^\s*OPENAI_API_KEY\s*=", line)
    ]
    assert not offending, (
        f"env.example must not define OPENAI_API_KEY (unused): {offending}"
    )


def test_env_example_has_no_redis_config():
    assert ENV_EXAMPLE.exists(), f"Missing env.example: {ENV_EXAMPLE}"
    offending = [
        line
        for line in ENV_EXAMPLE.read_text().splitlines()
        if re.match(r"^\s*REDIS_", line)
    ]
    assert not offending, (
        f"env.example must not define any REDIS_* variable (Redis is unused): "
        f"{offending}"
    )
