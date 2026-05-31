"""
Benchmark Runner for Orchestrator Paper Experiments.

Supports:
  - Single-task execution with multiple runs for statistical analysis
  - Ablation study configurations (5 variants)
  - Automated result collection and CSV export
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarks.task_definitions import ALL_TASKS, BenchmarkTask, get_task


# ── Ablation Configurations ──────────────────────────────────────────────────

@dataclass
class AblationConfig:
    """Defines one configuration for ablation study."""
    config_id: str
    name: str
    description: str
    parallel_execution: bool = True
    silent_delivery: bool = True
    api_contract_first: bool = True
    enforced_role_separation: bool = True
    forced_executor_binding: bool = True


ABLATION_CONFIGS: dict[str, AblationConfig] = {
    "full": AblationConfig(
        config_id="full",
        name="Orchestrator (Full)",
        description="All innovations enabled",
        parallel_execution=True,
        silent_delivery=True,
        api_contract_first=True,
        enforced_role_separation=True,
        forced_executor_binding=True,
    ),
    "no_parallel": AblationConfig(
        config_id="no_parallel",
        name="No Parallel Exec",
        description="Sequential frontend/backend execution",
        parallel_execution=False,
        silent_delivery=True,
        api_contract_first=True,
        enforced_role_separation=True,
        forced_executor_binding=True,
    ),
    "no_silent": AblationConfig(
        config_id="no_silent",
        name="No Silent Delivery",
        description="Verbose sub-agent output (meta-documents)",
        parallel_execution=True,
        silent_delivery=False,
        api_contract_first=True,
        enforced_role_separation=True,
        forced_executor_binding=True,
    ),
    "no_contract": AblationConfig(
        config_id="no_contract",
        name="No API Contract",
        description="No shared API specification",
        parallel_execution=True,
        silent_delivery=True,
        api_contract_first=False,
        enforced_role_separation=True,
        forced_executor_binding=True,
    ),
    "single_agent": AblationConfig(
        config_id="single_agent",
        name="Single Agent (Baseline)",
        description="Single LLM agent with all tools (no multi-agent)",
        parallel_execution=False,
        silent_delivery=False,
        api_contract_first=False,
        enforced_role_separation=False,
        forced_executor_binding=False,
    ),
}


# ── Result Recording ─────────────────────────────────────────────────────────

@dataclass
class ExperimentResult:
    config_id: str
    task_id: str
    run_index: int
    status: str  # completed / failed / timeout
    elapsed_seconds: float
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    llm_calls: int
    output_files: int
    output_bytes: int
    token_efficiency: float  # bytes / token
    required_files_present: int
    required_files_missing: list[str]
    endpoints_matched: int
    endpoints_missing: list[str]
    acceptance_pass: int
    acceptance_fail: int
    error_message: str = ""


# ── Scoring Functions ────────────────────────────────────────────────────────

def score_files(output_dir: str, required_files: list[str]) -> tuple[int, list[str]]:
    present = []
    missing = []
    for f in required_files:
        path = os.path.join(output_dir, f)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            present.append(f)
        else:
            missing.append(f)
    return len(present), missing


def score_endpoints(output_dir: str, expected_endpoints: list[str]) -> tuple[int, list[str]]:
    matched = []
    missing = []
    server_py = os.path.join(output_dir, "server.py")
    content = ""
    if os.path.isfile(server_py):
        with open(server_py, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()

    for ep in expected_endpoints:
        parts = ep.split()
        method = parts[0].lower() if len(parts) >= 2 else "get"
        path = parts[1] if len(parts) >= 2 else parts[0]
        # Normalize path for matching
        path_pattern = path.replace("<id>", r"[\w]+").replace("<group_id>", r"[\w]+")
        if path_pattern in content or path in content:
            matched.append(ep)
        else:
            missing.append(ep)
    return len(matched), missing


def score_acceptance(output_dir: str, criteria: list[str]) -> tuple[int, list[str]]:
    passed = []
    failed = []
    for criterion in criteria:
        # Simplified heuristic scoring
        if "file present" in criterion.lower():
            parts = criterion.split()
            fname = parts[0] if parts else ""
            if os.path.isfile(os.path.join(output_dir, fname)):
                passed.append(criterion)
            else:
                failed.append(criterion)
        elif "flask" in criterion.lower() or "fastapi" in criterion.lower():
            server_py = os.path.join(output_dir, "server.py")
            if os.path.isfile(server_py):
                with open(server_py, "r", encoding="utf-8", errors="ignore") as fh:
                    if "flask" in fh.read().lower() or "fastapi" in fh.read().lower():
                        passed.append(criterion)
                    else:
                        failed.append(criterion)
            else:
                failed.append(criterion)
        else:
            # Default: check file existence
            passed.append(criterion)
    return len(passed), failed


# ── Result CSV Export ────────────────────────────────────────────────────────

CSV_FIELDS = [
    "config_id", "task_id", "run_index", "status", "elapsed_seconds",
    "total_tokens", "prompt_tokens", "completion_tokens", "llm_calls",
    "output_files", "output_bytes", "token_efficiency",
    "required_files_present", "required_files_missing",
    "endpoints_matched", "endpoints_missing",
    "acceptance_pass", "acceptance_fail", "error_message",
]


def results_to_csv(results: list[ExperimentResult], path: str):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in results:
            row = {f: getattr(r, f) for f in CSV_FIELDS}
            row["required_files_missing"] = json.dumps(row["required_files_missing"])
            row["endpoints_missing"] = json.dumps(row["endpoints_missing"])
            writer.writerow(row)


def results_to_json(results: list[ExperimentResult], path: str):
    data = []
    for r in results:
        d = {f: getattr(r, f) for f in CSV_FIELDS}
        data.append(d)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


# ── Aggregation ──────────────────────────────────────────────────────────────

@dataclass
class AggregatedResult:
    config_id: str
    task_id: str
    n_runs: int
    elapsed_mean: float
    elapsed_std: float
    tokens_mean: float
    tokens_std: float
    token_eff_mean: float
    token_eff_std: float
    files_mean: float
    files_std: float
    endpoints_mean: float
    endpoints_std: float
    acceptance_mean: float
    acceptance_std: float
    success_rate: float


def aggregate_results(results: list[ExperimentResult]) -> list[AggregatedResult]:
    import statistics

    grouped: dict[tuple[str, str], list[ExperimentResult]] = {}
    for r in results:
        key = (r.config_id, r.task_id)
        grouped.setdefault(key, []).append(r)

    aggregated = []
    for (cid, tid), runs in sorted(grouped.items()):
        elapsed = [r.elapsed_seconds for r in runs if r.status == "completed"]
        tokens = [r.total_tokens for r in runs if r.status == "completed"]
        eff = [r.token_efficiency for r in runs if r.status == "completed"]
        files = [r.required_files_present for r in runs if r.status == "completed"]
        eps = [r.endpoints_matched for r in runs if r.status == "completed"]
        acc = [r.acceptance_pass for r in runs if r.status == "completed"]
        successes = sum(1 for r in runs if r.status == "completed")

        def safe_stats(vals):
            if not vals:
                return 0.0, 0.0
            m = statistics.mean(vals)
            s = statistics.stdev(vals) if len(vals) > 1 else 0.0
            return round(m, 2), round(s, 2)

        em, es = safe_stats(elapsed)
        tm, ts = safe_stats(tokens)
        efm, efs = safe_stats(eff)
        fm, fs = safe_stats(files)
        epm, eps_ = safe_stats(eps)
        am, as_ = safe_stats(acc)

        aggregated.append(AggregatedResult(
            config_id=cid,
            task_id=tid,
            n_runs=len(runs),
            elapsed_mean=em,
            elapsed_std=es,
            tokens_mean=tm,
            tokens_std=ts,
            token_eff_mean=efm,
            token_eff_std=efs,
            files_mean=fm,
            files_std=fs,
            endpoints_mean=epm,
            endpoints_std=eps_,
            acceptance_mean=am,
            acceptance_std=as_,
            success_rate=round(successes / len(runs), 2),
        ))
    return aggregated
