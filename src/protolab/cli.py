"""Thin console entry points; all arguments belong to ProtoMotions."""
from __future__ import annotations

import os
import sys


def _launch(module: str) -> None:
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    # Keep the tested compiler workaround, allowing an explicit caller override.
    environment.setdefault('TORCH_COMPILE_DISABLE', '1')
    os.execve(
        sys.executable,
        [sys.executable, '-u', '-m', module, *sys.argv[1:]],
        environment,
    )


def inference() -> None:
    _launch('protomotions.inference_agent')


def train() -> None:
    _launch('protomotions.train_agent')
