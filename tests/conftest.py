"""Nạp 2 script của skill như module để unit test (chúng nằm trong skills/*/scripts/)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(module_name: str, relative_path: str):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"Không nạp được module từ {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def pict_to_xlsx():
    return _load("pict_to_xlsx", "skills/autotest-testcase-pairwise/scripts/pict_to_xlsx.py")


@pytest.fixture(scope="session")
def xlsx_to_feature():
    return _load("xlsx_to_feature", "skills/autotest-gen-test/scripts/xlsx_to_feature.py")
