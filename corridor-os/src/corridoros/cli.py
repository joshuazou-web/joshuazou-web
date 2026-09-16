"""Command line entry points.

    corridoros demo               run the flagship story and print what happened
    corridoros snapshot [PATH]    write the console's data file
    corridoros verify-audit       recompute the hash chain over the demo's audit log
    corridoros boundary           print what the copilot may and may not do
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core.authority import ACTIONS, AI_ALLOWED, CONSEQUENTIAL_ACTIONS
from .scenario.snapshot import build_snapshot, write_snapshot
from .scenario.world import build_demo

DEFAULT_SNAPSHOT = Path("data/snapshot.json")


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

    sub.add_parser("verify-audit", help="recompute the audit hash chain").set_defaults(func=_verify_audit)
    sub.add_parser("boundary", help="print the AI permission boundary").set_defaults(func=_boundary)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
