"""
MicroEvals - A lightweight framework for evaluating code against specific criteria.

This package provides tools to run automated evaluations on codebases created by agents.
"""

__version__ = "0.1.0"

from .eval_registry import EvalRegistry
from .utils import (
    load_source,
    clone_repo,
    prepare_repo,
    build_prompt,
    run_eval,
    run_batch_eval,
    read_result,
    save_results,
    safe_cleanup_temp_dir
)

__all__ = [
    'EvalRegistry',
    'load_source',
    'clone_repo',
    'prepare_repo',
    'build_prompt',
    'run_eval',
    'run_batch_eval',
    'read_result',
    'save_results',
    'safe_cleanup_temp_dir'
]

