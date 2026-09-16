"""Command line entry points.

    corridoros demo               run the flagship story and print what happened
    corridoros snapshot [PATH]    write the console's data file
    corridoros verify-audit       recompute the hash chain over the demo's audit log
    corridoros boundary           print what the copilot may and may not do
    corridoros aml                run a day's transaction monitoring over the corridor
    corridoros aml-eval [PATH]    evaluate the AML layer over several seeded worlds
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core.authority import ACTIONS, AI_ALLOWED, CONSEQUENTIAL_ACTIONS
from .risk.evaluate import DEFAULT_CAPACITY
from .risk.evaluate import evaluate as evaluate_aml
from .scenario.feed import run_monitoring
from .scenario.snapshot import build_snapshot, write_snapshot
from .scenario.world import build_demo

DEFAULT_SNAPSHOT = Path("data/snapshot.json")
DEFAULT_AML_REPORT = Path("reports/aml_evaluation.json")


def _demo(args: argparse.Namespace) -> int:
    world = build_demo()
    print("CorridorOS — China–Singapore payment operations (synthetic data)\n")
    for line in world.transcript:
        print(f"  • {line}")
    system = world.system
    print()
    print(f"  events published      {len(system.bus)}")
    print(f"  audit entries         {len(system.audit.entries)} ({system.audit.verify().status})")
    print(f"  ledger balanced       {system.ledger.is_balanced()}")
    print(f"  copilot refusals      {len(system.audit.refusals)}")
    if args.json:
        print()
        print(json.dumps(build_snapshot(world)["overview"], indent=2))
    return 0


def _snapshot(args: argparse.Namespace) -> int:
    path = write_snapshot(Path(args.path))
    print(f"wrote {path} ({path.stat().st_size:,} bytes)")
    return 0


def _aml(args: argparse.Namespace) -> int:
    world = build_demo()
    queue, context, population = run_monitoring(world.system, capacity=args.capacity)
    run = queue.as_row()
    print("A day's transaction monitoring over the corridor (synthetic data)\n")
    print(f"  monitored transfers   {len(context.transfers):,}")
    print(f"  raw alerts            {run['raw_alerts']}")
    print(f"  after deduplication   {run['deduplicated_alerts']} ({run['duplicates_removed']} absorbed)")
    print(f"  cases                 {run['cases']}")
    print(f"  review capacity       {run['capacity']}")
    print(f"  backlog               {run['backlog']} — not cleared, not looked at")
    print(f"  planted patterns      {len(population.planted)} (the generator's ground truth)")
    print("\n  Top of the queue:")
    for case in queue.within_capacity[: args.top]:
        print(
            f"    P{case.queue_position:<2} {case.priority_band:<8} {case.priority_score:.3f}  "
            f"{case.subject_name[:34]:<34} {', '.join(case.typology_keys)}"
        )
    if queue.backlog:
        first = queue.backlog[0]
        print(
            f"\n  First case below the line: P{first.queue_position} {first.subject_name} "
            f"({', '.join(first.typology_keys)}) — waiting, not cleared."
        )
    return 0


def _aml_eval(args: argparse.Namespace) -> int:
    report = evaluate_aml(capacity=args.capacity)
    path = Path(args.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    headline = report["headline"]
    print("AML evaluation — synthetic, seeded, deliberately enriched\n")
    for key in (
        "scenario_recall",
        "recall_clear",
        "recall_borderline",
        "raw_alert_precision",
        "precision_at_capacity",
        "planted_patterns_left_in_backlog",
    ):
        value = headline[key]
        print(f"  {key:<34} {value['mean']:.4f} ± {value['stdev']:.4f}")
    print(f"\n  wrote {path}")
    return 0


def _verify_audit(_args: argparse.Namespace) -> int:
    world = build_demo()
    verification = world.system.audit.verify()
    print(verification.summary())
    return 0 if verification.valid else 1


def _boundary(_args: argparse.Namespace) -> int:
    print("The copilot may:")
    for action in sorted(AI_ALLOWED):
        print(f"  ✓ {action:<32} {ACTIONS[action].summary}")
    print("\nThe copilot may not (and has no code path to):")
    for action in sorted(CONSEQUENTIAL_ACTIONS):
        print(f"  ✗ {action:<32} {ACTIONS[action].summary}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="corridoros", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the flagship SGD 12,500 story")
    demo.add_argument("--json", action="store_true", help="also print the overview as JSON")
    demo.set_defaults(func=_demo)

    snapshot = sub.add_parser("snapshot", help="write the console data file")
    snapshot.add_argument("path", nargs="?", default=str(DEFAULT_SNAPSHOT))
    snapshot.set_defaults(func=_snapshot)

    aml = sub.add_parser("aml", help="run a day's transaction monitoring")
    aml.add_argument("--capacity", type=int, default=DEFAULT_CAPACITY)
    aml.add_argument("--top", type=int, default=8)
    aml.set_defaults(func=_aml)

    aml_eval = sub.add_parser("aml-eval", help="evaluate the AML layer over seeded worlds")
    aml_eval.add_argument("path", nargs="?", default=str(DEFAULT_AML_REPORT))
    aml_eval.add_argument("--capacity", type=int, default=DEFAULT_CAPACITY)
    aml_eval.set_defaults(func=_aml_eval)

    sub.add_parser("verify-audit", help="recompute the audit hash chain").set_defaults(func=_verify_audit)
    sub.add_parser("boundary", help="print the AI permission boundary").set_defaults(func=_boundary)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
