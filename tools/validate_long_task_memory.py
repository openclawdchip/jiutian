#!/usr/bin/env python3
"""Offline validator for Jiutian long-task memory benchmark samples."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


LEDGER_TYPES = ("goal", "plan", "evidence", "decision", "recovery")


class ValidationError(Exception):
    """Raised when a benchmark sample violates the v0.1 contract."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValidationError("top-level JSON value must be an object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def collect_refs(sample: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for window in sample.get("transcript_windows", []):
        refs.add(str(window.get("id")))
        refs.update(str(ref) for ref in window.get("turn_refs", []))
        compact = window.get("compact")
        if isinstance(compact, dict):
            refs.add(str(compact.get("id")))
            refs.update(str(ref) for ref in compact.get("kept_refs", []))
            refs.update(str(ref) for ref in compact.get("dropped_from_projection", []))
            refs.update(str(ref) for ref in compact.get("retained_in_ledger", []))
    for ledger in sample.get("ledgers", {}).values():
        for key in ("entries", "steps"):
            for entry in ledger.get(key, []):
                if isinstance(entry, dict) and entry.get("id"):
                    refs.add(str(entry["id"]))
                if isinstance(entry, dict):
                    refs.update(str(ref) for ref in entry.get("evidence", []))
                    if entry.get("last_safe_point"):
                        refs.add(str(entry["last_safe_point"]))
    for preview in sample.get("artifact_previews", []):
        if isinstance(preview, dict) and preview.get("id"):
            refs.add(str(preview["id"]))
    for delta in sample.get("expected_outputs", {}).get("ledger_delta", {}).get("deltas", []):
        value = delta.get("value")
        if isinstance(value, dict) and value.get("id"):
            refs.add(str(value["id"]))
    recovery = sample.get("expected_outputs", {}).get("recovery_anchor", {})
    resume_from = recovery.get("resume_from", {})
    if isinstance(resume_from, dict):
        for key in ("compact", "transcript_window", "trace"):
            if resume_from.get(key):
                refs.add(str(resume_from[key]))
    return {ref for ref in refs if ref and ref != "None"}


def validate_transcript_windows(sample: dict[str, Any]) -> dict[str, Any]:
    windows = sample.get("transcript_windows", [])
    require(isinstance(windows, list) and windows, "transcript_windows must be a non-empty list")
    by_id = {}
    compact_count = 0
    for window in windows:
        require(isinstance(window, dict), "each transcript window must be an object")
        window_id = window.get("id")
        require(isinstance(window_id, str) and window_id, "transcript window missing id")
        require(window_id not in by_id, f"duplicate transcript window id: {window_id}")
        by_id[window_id] = window
        parent = window.get("parent_window")
        if parent is not None:
            require(parent in by_id, f"parent_window {parent} must reference an earlier window")
        compact = window.get("compact")
        if compact is not None:
            compact_count += 1
            require(compact.get("input_window") == parent, f"compact input_window must match parent for {window_id}")
            require(compact.get("output_window") == window_id, f"compact output_window must match {window_id}")
            retained = set(compact.get("retained_in_ledger", []))
            dropped = set(compact.get("dropped_from_projection", []))
            require(dropped <= retained, f"dropped refs must remain in ledger for {window_id}")
    return {"windows": by_id, "compact_count": compact_count}


def validate_ledgers(sample: dict[str, Any]) -> dict[str, str]:
    ledgers = sample.get("ledgers", {})
    require(isinstance(ledgers, dict), "ledgers must be an object")
    versions: dict[str, str] = {}
    for ledger_type in LEDGER_TYPES:
        ledger = ledgers.get(ledger_type)
        require(isinstance(ledger, dict), f"missing ledger: {ledger_type}")
        version = ledger.get("version")
        require(isinstance(version, str) and version, f"{ledger_type} ledger missing version")
        versions[ledger_type] = version
    return versions


def validate_expected_outputs(sample: dict[str, Any], versions: dict[str, str], refs: set[str]) -> dict[str, Any]:
    expected = sample.get("expected_outputs", {})
    require(isinstance(expected, dict), "expected_outputs must be an object")

    ledger_delta = expected.get("ledger_delta", {})
    require(ledger_delta.get("base_versions") == versions, "ledger_delta base_versions must match ledgers")
    deltas = ledger_delta.get("deltas", [])
    require(isinstance(deltas, list), "ledger_delta.deltas must be a list")
    counts = Counter()
    for index, delta in enumerate(deltas):
        ledger = delta.get("ledger")
        require(ledger in LEDGER_TYPES, f"delta[{index}] has invalid ledger: {ledger}")
        counts[str(ledger)] += 1
        evidence = delta.get("evidence")
        require(isinstance(evidence, list) and evidence, f"delta[{index}] must include evidence refs")
        missing = [ref for ref in evidence if str(ref) not in refs]
        require(not missing, f"delta[{index}] references unknown evidence: {missing}")

    projection = expected.get("context_projection", {})
    active_evidence = projection.get("active_evidence", [])
    require(isinstance(active_evidence, list), "context_projection.active_evidence must be a list")
    for index, item in enumerate(active_evidence):
        require(isinstance(item, dict) and item.get("ref"), f"active_evidence[{index}] missing ref")
        require(str(item["ref"]) in refs, f"active_evidence[{index}] references unknown ref: {item['ref']}")
    budget = projection.get("budget", {})
    refs_budget = int(budget.get("refs", sample.get("config", {}).get("max_refs", len(active_evidence))))
    require(len(active_evidence) <= refs_budget, "context projection exceeds refs budget")

    recovery = expected.get("recovery_anchor", {})
    require(recovery.get("deterministic") is True, "recovery_anchor.deterministic must be true")
    resume_from = recovery.get("resume_from", {})
    require(resume_from.get("ledger_versions") == versions, "recovery_anchor ledger_versions must match ledgers")
    for ref in recovery.get("required_refs", []):
        require(str(ref) in refs, f"recovery_anchor required ref is unknown: {ref}")

    return {
        "delta_count_by_ledger": {ledger_type: counts.get(ledger_type, 0) for ledger_type in LEDGER_TYPES},
        "projection_refs": len(active_evidence),
        "recovery_deterministic": bool(recovery.get("deterministic")),
    }


def validate_metrics(sample: dict[str, Any], observed: dict[str, Any], compact_count: int) -> None:
    expected = sample.get("metrics_expectation", {})
    if not expected:
        return
    checks = {
        "compact_count": compact_count,
        "boundary_valid": True,
        "delta_count_by_ledger": observed["delta_count_by_ledger"],
        "projection_refs": observed["projection_refs"],
        "recovery_deterministic": observed["recovery_deterministic"],
        "unauthorized_source_count": 0,
    }
    for key, value in checks.items():
        if key in expected:
            require(expected[key] == value, f"metric {key} expected {expected[key]!r}, got {value!r}")


def validate_sample(sample: dict[str, Any]) -> dict[str, Any]:
    require(sample.get("schema") == "jiutian.benchmark.long_task_memory.v0.1", "unsupported schema")
    transcript = validate_transcript_windows(sample)
    versions = validate_ledgers(sample)
    refs = collect_refs(sample)
    observed = validate_expected_outputs(sample, versions, refs)
    validate_metrics(sample, observed, transcript["compact_count"])
    return {
        "name": sample.get("name", "<unnamed>"),
        "compact_count": transcript["compact_count"],
        **observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Jiutian long-task memory benchmark samples.")
    parser.add_argument("sample", type=Path, help="benchmark JSON sample")
    parser.add_argument("--json", action="store_true", help="emit machine-readable validation summary")
    args = parser.parse_args()

    try:
        summary = validate_sample(load_json(args.sample))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL {args.sample}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"status": "ok", **summary}, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "OK {name}: compact={compact_count} deltas={delta_count_by_ledger} "
            "projection_refs={projection_refs}".format(**summary)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
